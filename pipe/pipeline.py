from pw.pw_cert import PwCert
from data.prepdf import prep_df

class OnvioPipe:

    def __init__(self):
        self.cert = PwCert()
        

    def list_tarefas(self,page, linha_gb):
        total = len(linha_gb)
        for indice, (_, registro) in enumerate(linha_gb.iterrows(), start=1):
            print(f"[{indice}/{total}] Processando atividade: {registro['tarefa']}")
            encontrada = self.cert.search_certs(page, registro['tarefa'])
            if not encontrada:
                continue
            self.cert.edit_dates(page, registro.to_dict())

    def find_emp(self):
        pass


    def pipe(self):
        df = prep_df()
        self.cert.initial_setup()
        for cnpj, linha in df.groupby('cnpj'):
            page = self.cert.open_emp(str(cnpj))
            self.list_tarefas(page, linha)
            self.cert.return_list_emps()

