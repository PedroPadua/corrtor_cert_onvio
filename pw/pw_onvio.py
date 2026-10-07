from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv, find_dotenv


class PwOnvio:

    def __init__(self):
        load_dotenv(find_dotenv())
        self.fechado = False
        self.pw = sync_playwright().start()
        self.browser = self.pw.chromium.launch(headless=False)
        self.context = self.browser.new_context(storage_state="pw/onvio_state.json")
        self.page = self.context.new_page()
        
        


    def initial_setup(self):
        self.page.goto(
            "https://onvio.com.br/staff/#/dashboard-core-center",
            wait_until="domcontentloaded",
        )
        self.page.get_by_role("link", name="Menu").wait_for(
            state="visible", timeout=30_000
        )
        self.page.get_by_role("link", name="Menu").click()
        with self.page.expect_popup() as popup_info:
            self.page.get_by_role("link", name="Processos").click()
        self.proc = popup_info.value
        self.proc.wait_for_url("**/dashboard-v2**")
        self.proc.get_by_text("Tarefas", exact=True).wait_for(state="visible", timeout=10_000)
        self.proc.locator("div:nth-child(9) > .c-esMonm > .c-dWgEUF > .c-jmBOhu").click()
        self.proc.get_by_text("Gerenciar").nth(5).click()
        return self.proc
    
    def open_emp(self, cnpj: str):
        try:
            self.proc.get_by_role("textbox", name="Pesquisar por nome").fill(cnpj)
            self.proc.locator("a.link-to-edit").filter(has_text=cnpj).first.click()
            self.proc.get_by_role("link", name="Certidões e certificados").click()
            self.proc.wait_for_timeout(5000)
            return self.proc
        except Exception as e:
            raise RuntimeError(f'Falha ao encontrar empresa: {e}')

    def return_list_emps(self):
        self.proc.get_by_role("link", name="Clientes", exact=True).click()

            
    def close(self):
        if self.fechado:
            return
        self.fechado = True
        try:
            self.context.storage_state(path="pw/onvio_state.json")
        except Exception:
            pass
        finally:
            self.browser.close()
            self.pw.stop()