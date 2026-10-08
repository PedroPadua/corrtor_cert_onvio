from pw.pw_cert import PwCert
from data.prepdf import prep_df
import pandas as pd
class OnvioPipe:

    def __init__(self):
        self.cert = PwCert()
        

    def list_tarefas(self,page, linha_gb):
        relat = []
        total = len(linha_gb)
        for indice, (_, registro) in enumerate(linha_gb.iterrows(), start=1):
            print(f"[{indice}/{total}] Processando atividade: {registro['tarefa']}")
            encontrada = self.cert.search_certs(page, registro['tarefa'])
            qntd_reps = 'Nenhum' if encontrada['reps'] == 0 else encontrada['reps']
            relat.append({
                'emp': registro['emp'],
                'tarefa': registro['tarefa'],
                'status': 'Encontrada' if encontrada['status'] else 'Não encontrada',
                'repetições': qntd_reps,
                'erro': encontrada['erro']
            })
        return pd.DataFrame(
            relat,
            columns=['emp', 'tarefa', 'status', 'repetições', 'erro']
        )
    def find_emp(self):
        pass


    def pipe(self):
        df = prep_df()
        self.cert.initial_setup()
        relatorios = []
        for cnpj, linha in df.groupby('cnpj'):
            nome_empresa = str(linha['cnpj'].iloc[0])
            try:
                page = self.cert.open_emp(nome_empresa)
            except RuntimeError as erro:
                mensagem_erro = f"Falha ao abrir {nome_empresa} (CNPJ {cnpj}): {erro}"
                print(mensagem_erro)
                resultado = linha[['emp', 'tarefa']].copy()
                resultado['status'] = 'Falha ao abrir empresa'
                resultado['repetições'] = 'Nenhum'
                resultado['erro'] = mensagem_erro
                resultado = resultado[
                    ['emp', 'tarefa', 'status', 'repetições', 'erro']
                ]
            else:
                resultado = self.list_tarefas(page, linha)
                self.cert.return_list_emps()
            relatorios.append(resultado)
            df_relat = pd.concat(relatorios, ignore_index=True)
            df_relat.to_excel('relatório.xlsx', index=False)
            print(f"Relatório atualizado após processar a empresa {nome_empresa}.")

