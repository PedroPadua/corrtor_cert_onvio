from playwright.sync_api import sync_playwright
from pw.pw_onvio import PwOnvio
from data.prepdf import prep_df

class PwCert(PwOnvio):

    def __init__(self):
        super().__init__()
        self.df = prep_df()

    
    def search_certs(self):
        pass

    def edit_dates(self,page, emp_inf: dict):

        data = page.locator('input[name="expire_date"]')
        try:
            data.fill(emp_inf['expiracao'])
        except Exception:
            data.click()
            page.keyboard.type(emp_inf['expiracao'], delay=50)

        page.get_by_role("button", name="Salvar").click()
        page.get_by_role("button", name="Cancelar", exact=True).wait_for(state="visible", timeout=10000)
        page.get_by_role('button', name = 'Cancelar', exact = True).click()
        page.get_by_role("link", name="Clientes", exact=True).click()