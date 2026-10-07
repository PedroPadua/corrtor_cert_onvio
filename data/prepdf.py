import pandas as pd
import os, re
from dotenv import load_dotenv

load_dotenv()

def _sanatize_cnpj(cnpj):
    return re.sub(r"\D", "", str(cnpj))

def _prep_data(data):
    return data.strftime("%d/%m/%Y")

def prep_df():

    df = pd.read_excel(os.getenv('df_path'),
                        sheet_name = 'Vencimentos')
    df = df.rename(columns={'EmpID': 'id', 'Empresa': 'emp', 'CNPJ':'cnpj', 'OBRIGAÇÃO/TAREFA': 'tarefa', 'Prazo legal':'data'})
    df['cnpj'] = df['cnpj'].apply(_sanatize_cnpj)
    df = df.sort_values('cnpj')
    df['data'] = df['data'].apply(_prep_data)
    return df