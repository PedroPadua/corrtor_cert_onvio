from collections import Counter
from pathlib import Path
import re

import pandas as pd

from data.prepdf import prep_df
from pw.pw_cert import PwCert


COLUNAS_RELATORIO = ['cnpj', 'emp', 'tarefa', 'status', 'repeti\u00e7\u00f5es', 'erro']
ARQUIVO_RELATORIO = Path('relat\u00f3rio.xlsx')


def normalizar_cnpj(cnpj):
    return re.sub(r'\D', '', str(cnpj))


def cnpjs_concluidos_no_relatorio(df_atividades, df_relatorio):
    """Retorna CNPJs inteiramente presentes no relat\u00f3rio, inclusive legado."""
    concluidos = set()
    if not {'emp', 'tarefa'}.issubset(df_relatorio.columns):
        return concluidos

    # Falhas para abrir a empresa devem ser tentadas novamente na retomada.
    relatorio_valido = df_relatorio
    if 'status' in relatorio_valido.columns:
        relatorio_valido = relatorio_valido[
            relatorio_valido['status'] != 'Falha ao abrir empresa'
        ]

    for cnpj, linhas in df_atividades.groupby('cnpj'):
        pares_empresa = Counter(zip(
            linhas['emp'].fillna('').astype(str), linhas['tarefa'].fillna('').astype(str),
        ))
        if 'cnpj' in relatorio_valido.columns:
            cnpjs_relatorio = relatorio_valido['cnpj'].apply(normalizar_cnpj)
            linhas_relatorio = relatorio_valido[cnpjs_relatorio == normalizar_cnpj(cnpj)]
            # Linhas sem CNPJ pertencem ao arquivo legado e continuam eleg\u00edveis.
            linhas_relatorio = pd.concat([
                linhas_relatorio,
                relatorio_valido[cnpjs_relatorio == ''],
            ])
        else:
            linhas_relatorio = relatorio_valido
        pares_relatorio = Counter(zip(
            linhas_relatorio['emp'].fillna('').astype(str),
            linhas_relatorio['tarefa'].fillna('').astype(str),
        ))
        if pares_empresa and all(pares_relatorio[par] >= n for par, n in pares_empresa.items()):
            concluidos.add(normalizar_cnpj(cnpj))
    return concluidos


class OnvioPipe:

    def __init__(self):
        self.cert = PwCert()

    def list_tarefas(self, page, linha_gb):
        relat = []
        total = len(linha_gb)
        for indice, (_, registro) in enumerate(linha_gb.iterrows(), start=1):
            print(f"[{indice}/{total}] Processando atividade: {registro['tarefa']}")
            encontrada = self.cert.search_certs(page, registro['tarefa'])
            qntd_reps = 'Nenhum' if encontrada['reps'] == 0 else encontrada['reps']
            relat.append({
                'cnpj': normalizar_cnpj(registro['cnpj']),
                'emp': registro['emp'],
                'tarefa': registro['tarefa'],
                'status': 'Encontrada' if encontrada['status'] else 'N\u00e3o encontrada',
                'repeti\u00e7\u00f5es': qntd_reps,
                'erro': encontrada['erro'],
            })
        return pd.DataFrame(relat, columns=COLUNAS_RELATORIO)

    @staticmethod
    def escolher_modo():
        print('\nComo deseja executar?')
        print('1 - Processar todo o df_atividades (cria um novo relat\u00f3rio)')
        print('2 - Continuar o relat\u00f3rio existente (pula CNPJs j\u00e1 conclu\u00eddos)')
        while True:
            escolha = input('Op\u00e7\u00e3o [1/2]: ').strip()
            if escolha in {'1', '2'}:
                return escolha
            print('Op\u00e7\u00e3o inv\u00e1lida. Digite 1 ou 2.')

    @staticmethod
    def carregar_relatorio_existente():
        if not ARQUIVO_RELATORIO.exists():
            return pd.DataFrame(columns=COLUNAS_RELATORIO)
        return pd.read_excel(ARQUIVO_RELATORIO)

    @staticmethod
    def salvar_relatorio(df_relatorio, resultado):
        df_atualizado = pd.concat([df_relatorio, resultado], ignore_index=True)
        df_atualizado.to_excel(ARQUIVO_RELATORIO, index=False)
        return df_atualizado

    def pipe(self):
        df = prep_df()
        df['cnpj'] = df['cnpj'].apply(normalizar_cnpj)
        modo = self.escolher_modo()

        if modo == '2':
            df_relat = self.carregar_relatorio_existente()
            concluidos = cnpjs_concluidos_no_relatorio(df, df_relat)
            quantidade_antes = df['cnpj'].nunique()
            df = df[~df['cnpj'].isin(concluidos)]
            print(f'{quantidade_antes - df["cnpj"].nunique()} CNPJ(s) j\u00e1 conclu\u00eddo(s) ser\u00e3o pulados.')
        else:
            df_relat = pd.DataFrame(columns=COLUNAS_RELATORIO)

        if df.empty:
            print('N\u00e3o h\u00e1 CNPJs pendentes para processar.')
            return

        self.cert.initial_setup()
        for cnpj, linha in df.groupby('cnpj'):
            nome_empresa = str(cnpj)
            try:
                page = self.cert.open_emp(nome_empresa)
                print(f'Iniciando processamento da empresa {nome_empresa}')
                resultado = self.list_tarefas(page, linha)
                for _, registro in linha.iterrows():
                    self.cert.edit_tarefa(page, registro)
                self.cert.return_list_emps()
            except RuntimeError as erro:
                mensagem_erro = f'Falha ao abrir {nome_empresa} (CNPJ {cnpj}): {erro}'
                print(mensagem_erro)
                resultado = linha[['cnpj', 'emp', 'tarefa']].copy()
                resultado['status'] = 'Falha ao abrir empresa'
                resultado['repeti\u00e7\u00f5es'] = 'Nenhum'
                resultado['erro'] = mensagem_erro
                resultado = resultado[COLUNAS_RELATORIO]

            # Salva a cada CNPJ: uma interrup\u00e7\u00e3o posterior pode ser retomada.
            df_relat = self.salvar_relatorio(df_relat, resultado)
