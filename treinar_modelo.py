import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.utils import resample
import joblib

print("Carregando dataset...")
df = pd.read_csv("data/dataset_limpo.csv")


df_balanceado = []
for esi in [1, 2, 3, 4, 5]:
    classe = df[df["esi"] == esi]
    n = min(len(classe), 20000)
    classe_balanceada = resample(classe, n_samples=n, random_state=42)
    df_balanceado.append(classe_balanceada)

df = pd.concat(df_balanceado)
print(f"Dataset balanceado: {len(df)} registros")


X = df.drop(columns=["esi"])
y = df["esi"]


X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"Treinando com {len(X_train)} registros...")

modelo = RandomForestClassifier(
    n_estimators=200,
    max_depth=20,
    random_state=42,
    n_jobs=-1
)
modelo.fit(X_train, y_train)

print("\nAvaliando modelo...")
y_pred = modelo.predict(X_test)
print(f"Acurácia: {accuracy_score(y_test, y_pred) * 100:.2f}%")
print("\nRelatório completo:")
print(classification_report(y_test, y_pred))

joblib.dump(modelo, "modelo.pkl")
print("\nModelo salvo em modelo.pkl")