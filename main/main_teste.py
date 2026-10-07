from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from data.prepdf import prep_df
from pw.pw_cert import PwCert
from data.prepdf import prep_df

def teste_main():
    cert = PwCert()
    cert.initial_setup()
    page = cert.open_emp('11439055000119')
    encontrada = cert.search_certs(page, "PROCURACAO E-CAC") #returna True/False
    df = prep_df()
    if encontrada:
        registro = df.loc[
            (df["cnpj"] == "11439055000119") &
            (df["tarefa"] == "PROCURACAO E-CAC")
        ].iloc[0]
        cert.edit_dates(page, {"expiracao": registro["data"]})



if __name__ == "__main__":
    teste_main()