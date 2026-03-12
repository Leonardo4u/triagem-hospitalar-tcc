import json
import os
import re
from flask import Flask, render_template, request, redirect, url_for, session
import joblib
import pandas as pd
from conexao import conectar, inicializar_banco
from datetime import date

app = Flask(__name__, static_folder="Static", template_folder="templates")
app.secret_key = "triagem_hospitalar_2026"

# Inicializa banco e modelo
inicializar_banco()
modelo = joblib.load("modelo.pkl")
if hasattr(modelo, "feature_names_in_"):
    FEATURE_COLS = list(modelo.feature_names_in_)
else:
    metadata_path = "model_metadata.json"
    if os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8") as f:
            FEATURE_COLS = json.load(f).get("feature_names", [])
    else:
        FEATURE_COLS = []


def override_esi_critico(freq_card, freq_resp, pressao_s, spo2, temp, sintomas_dict):
    """Evita subtriagem em cenarios clinicos graves com regras de seguranca."""
    criticos = {
        "cc_lossofconsciousness",
        "cc_respiratorydistress",
    }
    importantes = {
        "cc_chestpain",
        "cc_shortnessofbreath",
        "cc_confusion",
    }

    tem_critico = any(sintomas_dict.get(s, 0) == 1 for s in criticos)
    tem_importante = any(sintomas_dict.get(s, 0) == 1 for s in importantes)

    # ESI 1: risco imediato de vida
    if (
        spo2 < 85
        or pressao_s < 80
        or freq_resp >= 35
        or freq_resp <= 7
        or freq_card >= 150
        or freq_card <= 35
        or temp >= 41.0
        or tem_critico
    ):
        return 5

    # ESI 2: alto risco / potencial deterioracao rapida
    if (
        spo2 < 90
        or pressao_s < 90
        or freq_resp >= 30
        or freq_resp <= 9
        or freq_card >= 130
        or freq_card <= 40
        or temp >= 40.0
        or tem_importante
    ):
        return 4

    return None

# ── Funções de formatação ─────────────────────────────────────────
def formatar_cpf(valor):
    n = re.sub(r'\D', '', valor)[:11]
    if len(n) > 9:  return f"{n[:3]}.{n[3:6]}.{n[6:9]}-{n[9:]}"
    if len(n) > 6:  return f"{n[:3]}.{n[3:6]}.{n[6:]}"
    if len(n) > 3:  return f"{n[:3]}.{n[3:]}"
    return n

def formatar_telefone(valor):
    n = re.sub(r'\D', '', valor)[:11]
    if len(n) > 6:  return f"({n[:2]}) {n[2:7]}-{n[7:]}"
    if len(n) > 2:  return f"({n[:2]}) {n[2:]}"
    if len(n) > 0:  return f"({n}"
    return ""

# ── PÁGINA 1 — CADASTRO ───────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])
def cadastro():
    erro = None

    if request.method == "POST":
        nome      = request.form.get("nome", "").strip()
        cpf_raw   = request.form.get("cpf", "")
        data_nasc = request.form.get("data_nasc", "")
        sexo      = request.form.get("sexo", "M")
        tel_raw   = request.form.get("telefone", "")

        cpf_fmt      = formatar_cpf(cpf_raw)
        tel_fmt      = formatar_telefone(tel_raw)
        cpf_numeros  = re.sub(r'\D', '', cpf_raw)

        if not nome:
            erro = "Nome é obrigatório."
        elif len(cpf_numeros) != 11:
            erro = "CPF inválido. Digite os 11 dígitos."
        else:
            conn   = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM pacientes WHERE cpf = ?", (cpf_fmt,))
            existente = cursor.fetchone()

            if existente:
                paciente_id = existente["id"]
            else:
                cursor.execute(
                    "INSERT INTO pacientes (nome, cpf, data_nasc, sexo, telefone) VALUES (?,?,?,?,?)",
                    (nome, cpf_fmt, data_nasc, sexo, tel_fmt)
                )
                conn.commit()
                paciente_id = cursor.lastrowid
            conn.close()

            # Calcula idade
            hoje = date.today()
            nasc = date.fromisoformat(data_nasc)
            idade = hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))

            session["paciente_id"] = paciente_id
            session["age"]         = idade
            session["gender"]      = 0 if sexo == "M" else 1

            return redirect(url_for("sintomas"))

    return render_template("Cadastro.html", erro=erro)


# ── PÁGINA 2 — SINTOMAS ───────────────────────────────────────────
@app.route("/sintomas", methods=["GET", "POST"])
def sintomas():
    if "paciente_id" not in session:
        return redirect(url_for("cadastro"))

    if request.method == "POST":
        # Sinais vitais
        temp      = float(request.form.get("temp", 36.5))
        freq_card = int(request.form.get("freq_card", 80))
        freq_resp = int(request.form.get("freq_resp", 16))
        pressao_s = int(request.form.get("pressao_s", 120))
        pressao_d = int(request.form.get("pressao_d", 80))
        spo2      = int(request.form.get("spo2", 98))
        nivel_dor = int(request.form.get("nivel_dor", 0))

        # Sintomas selecionados
        lista_sintomas = [
            "cc_headache","cc_dizziness","cc_confusion","cc_lossofconsciousness",
            "cc_chestpain","cc_shortnessofbreath","cc_palpitations","cc_respiratorydistress",
            "cc_abdominalpain","cc_nausea","cc_emesis","cc_diarrhea",
            "cc_fever","cc_fatigue","cc_weakness","cc_chills",
            "cc_legpain","cc_legswelling","cc_armpain","cc_numbness",
        ]
        sintomas_dict = {s: 1 if request.form.get(s) else 0 for s in lista_sintomas}

        # Monta entrada para o modelo
        dados = {
            "age": session["age"], "gender": session["gender"],
            "arrivalmode": 0,
            "triage_vital_hr": freq_card, "triage_vital_sbp": pressao_s,
            "triage_vital_dbp": pressao_d, "triage_vital_temp": temp,
            "triage_vital_o2": spo2, "triage_vital_rr": freq_resp,
            "pulse_last": freq_card, "resp_last": freq_resp,
            "spo2_last": spo2, "temp_last": temp,
            "sbp_last": pressao_s, "dbp_last": pressao_d,
        }
        for lab in ['wbc_last','hemoglobin_last','platelets_last','sodium_last',
                    'potassium_last','creatinine_last','glucose_last','bun_last',
                    'co2_last','lactate,poc_last','troponint_last','inr_last']:
            dados[lab] = 0
        dados["n_edvisits"] = dados["n_admissions"] = 0
        dados.update(sintomas_dict)

        if not FEATURE_COLS:
            raise RuntimeError("Modelo sem colunas de entrada. Gere modelo.pkl com treinar_modelo.py.")
        entrada    = {c: dados.get(c, 0) for c in FEATURE_COLS}
        df_entrada = pd.DataFrame([entrada])
        resultado_modelo = int(modelo.predict(df_entrada)[0])
        proba_raw = modelo.predict_proba(df_entrada)[0]
        classes = [int(c) for c in modelo.classes_]
        proba_por_classe = {classe: float(p) for classe, p in zip(classes, proba_raw)}
        proba = [proba_por_classe.get(esi, 0.0) for esi in [1, 2, 3, 4, 5]]

        # Regra de seguranca para reduzir chance de classificar grave como baixa prioridade.
        override = override_esi_critico(freq_card, freq_resp, pressao_s, spo2, temp, sintomas_dict)
        resultado = max(resultado_modelo, override or 0)

        # Salva no banco
        nomes_r = ["Não urgente","Pouco urgente","Urgente","Emergência","Emergência imediata"]
        cores_r = ["verde","amarelo","laranja","vermelho","vermelho"]
        conn   = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO triagens
                (paciente_id,temperatura,pressao_sistol,pressao_diast,
                 freq_cardiaca,nivel_dor,nivel_risco,descricao_risco,cor_risco)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (session["paciente_id"], temp, pressao_s, pressao_d,
              freq_card, nivel_dor, resultado,
              nomes_r[resultado-1], cores_r[resultado-1]))
        conn.commit()
        conn.close()

        session["resultado"] = resultado
        session["proba"]     = proba
        return redirect(url_for("resultado"))

    return render_template("Sintomas.html")


# ── PÁGINA 3 — RESULTADO ──────────────────────────────────────────
@app.route("/resultado")
def resultado():
    if "resultado" not in session:
        return redirect(url_for("cadastro"))

    esi    = session["resultado"]
    proba  = session["proba"]

    nomes  = {1:"Não Urgente", 2:"Pouco Urgente", 3:"Urgente",
              4:"Emergência", 5:"Emergência Imediata"}
    cores  = {1:"verde", 2:"amarelo", 3:"laranja", 4:"vermelho", 5:"vermelho"}
    tempos = {
        1:"Pode aguardar",
        2:"Atender em até 60 minutos",
        3:"Atender em até 30 minutos",
        4:"Atender em até 10 minutos",
        5:"Atendimento IMEDIATO",
    }

    proba_labels = [
        {"esi": i+1, "nome": nomes[i+1], "cor": cores[i+1], "pct": round(p*100, 1)}
        for i, p in enumerate(proba)
    ]

    return render_template("Resultado.html",
        esi=esi, nome=nomes[esi], cor=cores[esi],
        tempo=tempos[esi], proba=proba_labels
    )


# ── NOVA TRIAGEM ──────────────────────────────────────────────────
@app.route("/nova")
def nova():
    session.clear()
    return redirect(url_for("cadastro"))


if __name__ == "__main__":
    app.run(debug=True)