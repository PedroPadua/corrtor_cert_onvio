from playwright.sync_api import sync_playwright
from pw.pw_onvio import PwOnvio


class PwCert(PwOnvio):

    def __init__(self):
        super().__init__()
    
    def search_certs(self, page, atividade):
        esperado = " ".join(str(atividade).casefold().split())
        linhas = page.locator('.ag-body-container > div[role="row"]')
        nomes = page.locator(
            '.ag-body-container > div[role="row"] div[col-id="name"]'
        )
        nomes.first.wait_for(
            state="visible", timeout=10_000
        )
        nomes_visiveis = []

        for i in range(linhas.count()):
            linha = linhas.nth(i)
            celula_nome = linha.locator('div[col-id="name"]')

            if not celula_nome.count():
                continue

            nome_original = celula_nome.inner_text().strip()
            nomes_visiveis.append(nome_original)
            nome = " ".join(nome_original.casefold().split())

            if nome == esperado:
                print(f"Atividade encontrada: {atividade}. Clicando na linha {i + 1}.")
                linha.click()
                return True

        print(f"Atividade não encontrada: {atividade!r} (normalizada: {esperado!r})")
        print(f"URL atual: {page.url}")
        print(f"Nomes visíveis na grade: {nomes_visiveis!r}")
        return False


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