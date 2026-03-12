import json

import joblib
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.utils import resample


def balancear_dataset(df, max_por_classe=20000):
    df_balanceado = []
    for esi in [1, 2, 3, 4, 5]:
        classe = df[df["esi"] == esi]
        n = min(len(classe), max_por_classe)
        classe_balanceada = resample(classe, n_samples=n, random_state=42)
        df_balanceado.append(classe_balanceada)
    return pd.concat(df_balanceado).sample(frac=1.0, random_state=42).reset_index(drop=True)


print("Carregando dataset...")
df = pd.read_csv("data/dataset_limpo.csv")
df = balancear_dataset(df, max_por_classe=20000)
print(f"Dataset balanceado: {len(df)} registros")

X = df.drop(columns=["esi"])
y = df["esi"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Treinando com {len(X_train)} registros...")

# Peso maior para classes graves para reduzir subtriagem (ESI 4 e 5).
pesos = {1: 1.0, 2: 1.2, 3: 1.8, 4: 2.5, 5: 3.0}
base_model = RandomForestClassifier(
    n_estimators=300,
    max_depth=22,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1,
    class_weight=pesos,
)

modelo = CalibratedClassifierCV(estimator=base_model, method="isotonic", cv=3)
modelo.fit(X_train, y_train)

# Mantem compatibilidade com app.py que usa feature_names_in_.
modelo.feature_names_in_ = X.columns.to_numpy()

print("\nAvaliando modelo...")
y_pred = modelo.predict(X_test)

print(f"Acurácia: {accuracy_score(y_test, y_pred) * 100:.2f}%")
print("\nRelatório por classe:")
print(classification_report(y_test, y_pred, digits=4))

matriz = confusion_matrix(y_test, y_pred, labels=[1, 2, 3, 4, 5])
print("\nMatriz de confusão (linhas=real, colunas=predito):")
print(matriz)

y_test_alto = (y_test >= 4).astype(int)
y_pred_alto = (y_pred >= 4).astype(int)
report_alto = classification_report(
    y_test_alto,
    y_pred_alto,
    target_names=["Nao alto risco (ESI 1-3)", "Alto risco (ESI 4-5)"],
    digits=4,
)
print("\nDeteccao de alto risco (ESI 4-5):")
print(report_alto)

joblib.dump(modelo, "modelo.pkl")

with open("model_metadata.json", "w", encoding="utf-8") as f:
    json.dump(
        {
            "feature_names": X.columns.tolist(),
            "classes": [int(c) for c in sorted(y.unique())],
            "notes": "Modelo calibrado com foco em sensibilidade para ESI 4-5.",
        },
        f,
        ensure_ascii=False,
        indent=2,
    )

print("\nModelo salvo em modelo.pkl")
print("Metadados salvos em model_metadata.json")