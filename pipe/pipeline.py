from pathlib import Path
import re

import pandas as pd

from data.prepdf import prep_df
from pw.pw_cert import PwCert


COLUNAS_RELATORIO = ['cnpj', 'emp', 'tarefa', 'status', 'repeti\u00e7\u00f5es', 'erro']
ARQUIVO_RELATORIO = Path('relat\u00f3rio.xlsx')


def normalizar_cnpj(cnpj):
    texto = str(cnpj).strip()
    # Excel costuma devolver CNPJ como n\u00famero (ex.: 123...75.0).
    if texto.endswith('.0'):
        texto = texto[:-2]
    digitos = re.sub(r'\D', '', texto)
    # Vers\u00f5es anteriores gravaram alguns CNPJs num\u00e9ricos com um zero final.
    if len(digitos) == 15 and digitos.endswith('0'):
        digitos = digitos[:-1]
    return digitos


def filtrar_atividades_ja_feitas(df_atividades, df_relatorio):
    """Remove do df as atividades que j\u00e1 constam no relat\u00f3rio.xlsx.

    A chave \u00e9 CNPJ + tarefa. Se o relat\u00f3rio for antigo e n\u00e3o tiver CNPJ,
    usa empresa + tarefa como compatibilidade. Assim, uma empresa processada
    parcialmente ter\u00e1 apenas as atividades restantes executadas.
    """
    if not {'emp', 'tarefa'}.issubset(df_relatorio.columns):
        return df_atividades.copy()

    relatorio_valido = df_relatorio
    if 'status' in relatorio_valido.columns:
        relatorio_valido = relatorio_valido[
            relatorio_valido['status'] != 'Falha ao abrir empresa'
        ]

    atividades = df_atividades.copy()
    atividades['_chave_cnpj'] = list(zip(
        atividades['cnpj'].apply(normalizar_cnpj),
        atividades['tarefa'].fillna('').astype(str),
    ))
    atividades['_chave_empresa'] = list(zip(
        atividades['emp'].fillna('').astype(str),
        atividades['tarefa'].fillna('').astype(str),
    ))

    chaves_cnpj = set()
    if 'cnpj' in relatorio_valido.columns:
        chaves_cnpj = set(zip(
            relatorio_valido['cnpj'].apply(normalizar_cnpj),
            relatorio_valido['tarefa'].fillna('').astype(str),
        ))
        chaves_cnpj.discard(('', ''))

    # Linhas sem CNPJ s\u00e3o de relat\u00f3rios antigos; nelas a chave \u00e9 empresa+tarefa.
    if 'cnpj' in relatorio_valido.columns:
        legado = relatorio_valido[
            relatorio_valido['cnpj'].apply(normalizar_cnpj) == ''
        ]
    else:
        legado = relatorio_valido
    chaves_empresa = set(zip(
        legado['emp'].fillna('').astype(str),
        legado['tarefa'].fillna('').astype(str),
    ))

    ja_feitas = (
        atividades['_chave_cnpj'].isin(chaves_cnpj)
        | atividades['_chave_empresa'].isin(chaves_empresa)
    )
    return atividades.loc[~ja_feitas].drop(columns=['_chave_cnpj', '_chave_empresa'])


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
        print('2 - Continuar o relat\u00f3rio existente (pula atividades j\u00e1 feitas)')
        while True:
            escolha = input('Op\u00e7\u00e3o [1/2]: ').strip()
            if escolha in {'1', '2'}:
                return escolha
            print('Op\u00e7\u00e3o inv\u00e1lida. Digite 1 ou 2.')

    @staticmethod
    def carregar_relatorio_existente():
        if not ARQUIVO_RELATORIO.exists():
            return pd.DataFrame(columns=COLUNAS_RELATORIO)
        return pd.read_excel(ARQUIVO_RELATORIO, dtype={'cnpj': str})

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
            quantidade_antes = len(df)
            df = filtrar_atividades_ja_feitas(df, df_relat)
            print(f'{quantidade_antes - len(df)} atividade(s) j\u00e1 presente(s) no relat\u00f3rio ser\u00e3o puladas.')
        else:
            df_relat = pd.DataFrame(columns=COLUNAS_RELATORIO)

        if df.empty:
            print('N\u00e3o h\u00e1 atividades pendentes para processar.')
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
