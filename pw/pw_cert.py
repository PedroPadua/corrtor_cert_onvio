from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from pw.pw_onvio import PwOnvio
from collections import Counter


class PwCert(PwOnvio):

    def __init__(self):
        super().__init__()
    
    def search_certs(self, page, atividade):
        esperado = " ".join(str(atividade).casefold().split())
        linhas = page.locator('.ag-body-container > div[role="row"]')
        nomes = page.locator(
            '.ag-body-container > div[role="row"] div[col-id="name"]'
        )
        try:
            nomes.first.wait_for(state="visible", timeout=10_000)
        except PlaywrightTimeoutError:
            erro = (
                "Nenhuma atividade visível no Onvio (grade vazia ou não carregada); "
                f"atividade não encontrada: {atividade}"
            )
            print(erro)
            return {'status': False, 'reps': 0, 'erro': erro}
        nomes_visiveis = []
        encontrada = False

        for i in range(linhas.count()):
            linha = linhas.nth(i)
            celula_nome = linha.locator('div[col-id="name"]')

            if not celula_nome.count():
                continue

            nome_original = celula_nome.inner_text().strip()
            nomes_visiveis.append(nome_original)
            nome = " ".join(nome_original.casefold().split())

            if nome == esperado:
                print(f"Atividade encontrada: {atividade} na linha {i + 1}.")
                encontrada = True

        contagem = Counter(nomes_visiveis)
        duplicados = {item : qtd for item, qtd in contagem.items() if qtd>1}
        reps = len(duplicados)
        if not encontrada:
            print(f"Atividade não encontrada: {atividade!r} (normalizada: {esperado!r})")
            print(f"URL atual: {page.url}")
            print(f"Nomes visíveis na grade: {nomes_visiveis!r}")
        erro = None if encontrada else f"Atividade não encontrada no Onvio: {atividade}"
        return {'status': encontrada, 'reps': reps, 'erro': erro}


    def edit_dates(self,page, emp_inf: dict):

        data = page.locator('input[name="expire_date"]')
        try:
            data.fill(emp_inf['data'])
        except Exception:
            data.click()
            page.keyboard.type(emp_inf['data'], delay=50)

        page.get_by_role("button", name="Salvar").click()
        page.get_by_role("button", name="Cancelar", exact=True).wait_for(state="visible", timeout=10000)
        page.get_by_role('button', name = 'Cancelar', exact = True).click()
        page.locator(
            '.ag-body-container > div[role="row"] div[col-id="name"]'
        ).first.wait_for(
            state="visible", timeout=10_000
        )