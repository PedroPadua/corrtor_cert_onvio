import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

def prep_df():

    df = pd.read_excel(os.getenv('df_path'),
                        sheet_name = 'Vencimentos')
    df = df.rename(columns={'EmpID': 'id', 'Empresa': 'emp', 'CNPJ':'cnpj', 'OBRIGAÇÃO/TAREFA': 'tarefa', 'Prazo legal':'data'})
    return df
