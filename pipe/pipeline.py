from pw.pw_cert import PwCert
from data.prepdf import prep_df

class OnvioPipe:

    def __init__(self):
        self.cert = PwCert()
        self.df = prep_df()

    def start_engine(self):

        self.cert.init_pw()
        self.cert.initial_setup()

    def pipe(self):
        for _, registro in self.df.iterrows():
            atividade = registro["tarefa"]

            # O CNPJ já identifica a empresa que deve estar aberta nesta etapa.
            encontrada = self.cert.search_certs(self.cert.proc, atividade)

            if not encontrada:
                continue

            # Aqui você usa os demais dados deste mesmo registro,
            # por exemplo registro["data"], para preencher a informação.

