import re
from datetime import date

import joblib
import pandas as pd
from flask import Flask, redirect, render_template, request, session, url_for

from conexao import conectar, inicializar_banco

app = Flask(__name__, static_folder="Static", template_folder="templates")
app.secret_key = "triagem_hospitalar_2026"

# Inicializa banco e modelo
inicializar_banco()
modelo = joblib.load("modelo.pkl")


def formatar_cpf(valor: str) -> str:
    n = re.sub(r"\D", "", valor)[:11]
    if len(n) > 9:
        return f"{n[:3]}.{n[3:6]}.{n[6:9]}-{n[9:]}"
    if len(n) > 6:
        return f"{n[:3]}.{n[3:6]}.{n[6:]}"
    if len(n) > 3:
        return f"{n[:3]}.{n[3:]}"
    return n


def formatar_telefone(valor: str) -> str:
    n = re.sub(r"\D", "", valor)[:11]
    if len(n) > 6:
        return f"({n[:2]}) {n[2:7]}-{n[7:]}"
    if len(n) > 2:
        return f"({n[:2]}) {n[2:]}"
    if len(n) > 0:
        return f"({n}"
    return ""


@app.route("/", methods=["GET", "POST"])
def cadastro():
    erro = None

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        cpf_raw = request.form.get("cpf", "")
        data_nasc = request.form.get("data_nasc", "")
        sexo = request.form.get("sexo", "M")
        tel_raw = request.form.get("telefone", "")

        cpf_fmt = formatar_cpf(cpf_raw)
        tel_fmt = formatar_telefone(tel_raw)
        cpf_numeros = re.sub(r"\D", "", cpf_raw)

        if not nome:
            erro = "Nome e obrigatorio."
        elif len(cpf_numeros) != 11:
            erro = "CPF invalido. Digite os 11 digitos."
        else:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM pacientes WHERE cpf = ?", (cpf_fmt,))
            existente = cursor.fetchone()

            if existente:
                paciente_id = existente["id"]
            else:
                cursor.execute(
                    "INSERT INTO pacientes (nome, cpf, data_nasc, sexo, telefone) VALUES (?,?,?,?,?)",
                    (nome, cpf_fmt, data_nasc, sexo, tel_fmt),
                )
                conn.commit()
                paciente_id = cursor.lastrowid
            conn.close()

            hoje = date.today()
            nasc = date.fromisoformat(data_nasc)
            idade = hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))

            session["paciente_id"] = paciente_id
            session["age"] = idade
            session["gender"] = 0 if sexo == "M" else 1

            return redirect(url_for("sintomas"))

    return render_template("Cadastro.html", erro=erro)


@app.route("/sintomas", methods=["GET", "POST"])
def sintomas():
    if "paciente_id" not in session:
        return redirect(url_for("cadastro"))

    if request.method == "POST":
        temp = float(request.form.get("temp", 36.5))
        freq_card = int(request.form.get("freq_card", 80))
        freq_resp = int(request.form.get("freq_resp", 16))
        pressao_s = int(request.form.get("pressao_s", 120))
        pressao_d = int(request.form.get("pressao_d", 80))
        spo2 = int(request.form.get("spo2", 98))
        nivel_dor = int(request.form.get("nivel_dor", 0))

        lista_sintomas = [
            "cc_headache",
            "cc_dizziness",
            "cc_confusion",
            "cc_lossofconsciousness",
            "cc_chestpain",
            "cc_shortnessofbreath",
            "cc_palpitations",
            "cc_respiratorydistress",
            "cc_abdominalpain",
            "cc_nausea",
            "cc_emesis",
            "cc_diarrhea",
            "cc_fever",
            "cc_fatigue",
            "cc_weakness",
            "cc_chills",
            "cc_legpain",
            "cc_legswelling",
            "cc_armpain",
            "cc_numbness",
        ]
        sintomas_dict = {s: 1 if request.form.get(s) else 0 for s in lista_sintomas}

        dados = {
            "age": session["age"],
            "gender": session["gender"],
            "arrivalmode": 0,
            "triage_vital_hr": freq_card,
            "triage_vital_sbp": pressao_s,
            "triage_vital_dbp": pressao_d,
            "triage_vital_temp": temp,
            "triage_vital_o2": spo2,
            "triage_vital_rr": freq_resp,
            "pulse_last": freq_card,
            "resp_last": freq_resp,
            "spo2_last": spo2,
            "temp_last": temp,
            "sbp_last": pressao_s,
            "dbp_last": pressao_d,
        }

        for lab in [
            "wbc_last",
            "hemoglobin_last",
            "platelets_last",
            "sodium_last",
            "potassium_last",
            "creatinine_last",
            "glucose_last",
            "bun_last",
            "co2_last",
            "lactate,poc_last",
            "troponint_last",
            "inr_last",
        ]:
            dados[lab] = 0

        dados["n_edvisits"] = 0
        dados["n_admissions"] = 0
        dados.update(sintomas_dict)

        entrada = {c: dados.get(c, 0) for c in modelo.feature_names_in_}
        df_entrada = pd.DataFrame([entrada])
        resultado = int(modelo.predict(df_entrada)[0])
        proba = modelo.predict_proba(df_entrada)[0].tolist()

        nomes_r = ["Nao urgente", "Pouco urgente", "Urgente", "Emergencia", "Emergencia imediata"]
        cores_r = ["verde", "amarelo", "laranja", "vermelho", "vermelho"]

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO triagens
                (paciente_id, temperatura, pressao_sistol, pressao_diast,
                 freq_cardiaca, nivel_dor, nivel_risco, descricao_risco, cor_risco)
            VALUES (?,?,?,?,?,?,?,?,?)
            """,
            (
                session["paciente_id"],
                temp,
                pressao_s,
                pressao_d,
                freq_card,
                nivel_dor,
                resultado,
                nomes_r[resultado - 1],
                cores_r[resultado - 1],
            ),
        )
        conn.commit()
        conn.close()

        session["resultado"] = resultado
        session["proba"] = proba
        return redirect(url_for("resultado"))

    return render_template("Sintomas.html")


@app.route("/resultado")
def resultado():
    if "resultado" not in session:
        return redirect(url_for("cadastro"))

    esi = session["resultado"]
    proba = session["proba"]

    nomes = {
        1: "Nao Urgente",
        2: "Pouco Urgente",
        3: "Urgente",
        4: "Emergencia",
        5: "Emergencia Imediata",
    }
    cores = {1: "verde", 2: "amarelo", 3: "laranja", 4: "vermelho", 5: "vermelho"}
    tempos = {
        1: "Pode aguardar",
        2: "Atender em ate 60 minutos",
        3: "Atender em ate 30 minutos",
        4: "Atender em ate 10 minutos",
        5: "Atendimento IMEDIATO",
    }

    proba_labels = [
        {"esi": i + 1, "nome": nomes[i + 1], "cor": cores[i + 1], "pct": round(p * 100, 1)}
        for i, p in enumerate(proba)
    ]

    return render_template(
        "Resultado.html",
        esi=esi,
        nome=nomes[esi],
        cor=cores[esi],
        tempo=tempos[esi],
        proba=proba_labels,
    )


@app.route("/nova")
def nova():
    session.clear()
    return redirect(url_for("cadastro"))


if __name__ == "__main__":
    app.run(debug=True)
