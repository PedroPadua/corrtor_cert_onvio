from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from data.prepdf import prep_df
from pw.pw_cert import PwCert


def normalizar_nome(valor):
    return " ".join(str(valor).casefold().split())


def capturar_atividades(page):
    linhas = page.locator('div[role="row"]')
    try:
        linhas.first.wait_for(state="visible", timeout=10_000)
    except PlaywrightTimeoutError:
        return []

    atividades = []
    for indice in range(linhas.count()):
        celula_nome = linhas.nth(indice).locator('div[col-id="name"]')
        if celula_nome.count():
            nome = celula_nome.inner_text().strip()
            if nome:
                atividades.append(nome)

    return atividades


def main():
    df = prep_df()
    estado = Path("pw/onvio_state.json")

    cert = PwCert.__new__(PwCert)
    cert.fechado = False
    cert.pw = sync_playwright().start()

    try:
        cert.browser = cert.pw.chromium.launch(headless=False)
        argumentos_contexto = {"storage_state": str(estado)} if estado.exists() else {}
        cert.context = cert.browser.new_context(**argumentos_contexto)
        cert.page = cert.context.new_page()

        if not estado.exists():
            cert.page.goto("https://onvio.com.br/staff/#/dashboard-core-center")
            input("Faça login no Onvio na janela aberta e pressione Enter aqui.")

        print("Abrindo o fluxo de empresas do Onvio...")
        page = cert.initial_setup()
        total_capturadas = 0

        for indice, (cnpj, registros) in enumerate(df.groupby("cnpj", sort=False)):
            if indice:
                page.get_by_role("link", name="Clientes", exact=True).click()
                page.get_by_role("textbox", name="Pesquisar por nome").wait_for(
                    state="visible", timeout=10_000
                )

            empresa = registros["emp"].iloc[0]
            print(f"\nPesquisando empresa: {empresa} | CNPJ: {cnpj}")
            page = cert.open_emp(cnpj)
            page.get_by_text("Certificados", exact=True).click()
            atividades = capturar_atividades(page)
            total_capturadas += len(atividades)

            print(f"Atividades capturadas para esta empresa: {len(atividades)}")
            for atividade in atividades:
                print(f"- {atividade}")

            esperadas = registros["tarefa"].dropna().drop_duplicates().tolist()
            capturadas_normalizadas = {normalizar_nome(item) for item in atividades}
            encontradas = [
                tarefa for tarefa in esperadas
                if normalizar_nome(tarefa) in capturadas_normalizadas
            ]

            print(f"Tarefas desta empresa no Excel: {len(esperadas)}")
            print(f"Tarefas encontradas nesta empresa: {len(encontradas)}")
            for tarefa in esperadas:
                status = (
                    "CAPTURADA"
                    if normalizar_nome(tarefa) in capturadas_normalizadas
                    else "NAO ENCONTRADA"
                )
                print(f"[{status}] {tarefa}")

        if not total_capturadas:
            raise RuntimeError("Nenhuma atividade foi capturada nas empresas pesquisadas.")
    finally:
        cert.close()


if __name__ == "__main__":
    main()