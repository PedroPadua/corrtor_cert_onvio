from pw.pw_cert import PwCert
from data.prepdf import prep_df

def teste_main():
    cert = PwCert()
    cert.initial_setup()
    cnpj = '11439055000119'
    registro = prep_df().loc[lambda df: df['cnpj'] == cnpj].iloc[0]
    page = cert.open_emp(str(registro['emp']))
    resultado = cert.search_certs(page, "PROCURACAO E-CAC")
    if not resultado['status']:
        print(resultado['erro'])
        return
    print("Atividade encontrada no Onvio.")


if __name__ == "__main__":
    teste_main()