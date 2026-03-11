import pyreadr
import pandas as pd

print("Carregando arquivo...")
resultado = pyreadr.read_r("5v_cleandf.rdata")
df = list(resultado.values())[0]

# Colunas de sinais vitais
sinais_vitais = [
    'triage_vital_hr',
    'triage_vital_sbp',
    'triage_vital_dbp',
    'triage_vital_temp',
    'triage_vital_o2',
]

# Colunas de queixas principais (sintomas)
sintomas = [
    'cc_chestpain', 'cc_shortnessofbreath', 'cc_fever',
    'cc_headache', 'cc_abdominalpain', 'cc_dizziness',
    'cc_nausea', 'cc_vomiting' if 'cc_vomiting' in df.columns else 'cc_emesis',
    'cc_weakness', 'cc_lossofconsciousness', 'cc_seizures',
    'cc_diarrhea', 'cc_backpain', 'cc_chills', 'cc_fatigue',
    'cc_legpain', 'cc_confusion', 'cc_palpitations', 'cc_syncope',
]

sintomas = [c for c in sintomas if c in df.columns]


paciente = ['age', 'gender']

alvo = ['esi']

colunas = paciente + sinais_vitais + sintomas + alvo
df_modelo = df[colunas].copy()


df_modelo = df_modelo.dropna(subset=['esi'])

for col in sinais_vitais:
    df_modelo[col] = df_modelo[col].fillna(df_modelo[col].median())


df_modelo['gender'] = df_modelo['gender'].map({'Male': 0, 'Female': 1}).fillna(2)


df_modelo['esi'] = df_modelo['esi'].astype(int)


df_modelo.to_csv("data/dataset_limpo.csv", index=False)

print(f"Dataset salvo com {len(df_modelo)} linhas e {len(df_modelo.columns)} colunas")
print("Distribuição do ESI:")
print(df_modelo['esi'].value_counts().sort_index())