import streamlit as st
import joblib
import pandas as pd
import numpy as np
from conexao import conectar, inicializar_banco
from datetime import date

# Inicializa banco
inicializar_banco()

# Carrega modelo
modelo = joblib.load("modelo.pkl")

# Configuração da página
st.set_page_config(page_title="Sistema de Triagem", page_icon="🏥", layout="centered")

# Controle de navegação
if "pagina" not in st.session_state:
    st.session_state.pagina = 1
if "paciente_id" not in st.session_state:
    st.session_state.paciente_id = None
if "dados_triagem" not in st.session_state:
    st.session_state.dados_triagem = {}

# ── PÁGINA 1: CADASTRO ──────
if st.session_state.pagina == 1:
    st.title("🏥 Sistema de Triagem Hospitalar")
    st.subheader("Passo 1 — Cadastro do Paciente")
    st.divider()

    nome = st.text_input("Nome completo")
    cpf = st.text_input("CPF")
    data_nasc = st.date_input("Data de nascimento", min_value=date(1900,1,1), max_value=date.today())
    sexo = st.selectbox("Sexo", ["M", "F", "Outro"])
    telefone = st.text_input("Telefone (opcional)")

    if st.button("Próximo →", type="primary"):
        if not nome or not cpf:
            st.error("Nome e CPF são obrigatórios.")
        else:
            conn = conectar()
            cursor = conn.cursor()
            # Verifica se paciente já existe
            cursor.execute("SELECT id FROM pacientes WHERE cpf = ?", (cpf,))
            existente = cursor.fetchone()
            if existente:
                st.session_state.paciente_id = existente["id"]
                st.info("Paciente já cadastrado. Continuando...")
            else:
                cursor.execute(
                    "INSERT INTO pacientes (nome, cpf, data_nasc, sexo, telefone) VALUES (?, ?, ?, ?, ?)",
                    (nome, cpf, str(data_nasc), sexo, telefone)
                )
                conn.commit()
                st.session_state.paciente_id = cursor.lastrowid
            conn.close()

            # Calcula idade
            hoje = date.today()
            idade = hoje.year - data_nasc.year - ((hoje.month, hoje.day) < (data_nasc.month, data_nasc.day))
            st.session_state.dados_triagem["age"] = idade
            st.session_state.dados_triagem["gender"] = 0 if sexo == "M" else 1

            st.session_state.pagina = 2
            st.rerun()

# ── PÁGINA 2: SINTOMAS E SINAIS VITAIS ──────────────────────────────
elif st.session_state.pagina == 2:
    st.title("🏥 Sistema de Triagem Hospitalar")
    st.subheader("Passo 2 — Sintomas e Sinais Vitais")
    st.divider()

    # Sinais vitais
    st.markdown("### 📊 Sinais Vitais")
    col1, col2 = st.columns(2)
    with col1:
        temp = st.number_input("Temperatura (°C)", 34.0, 42.0, 36.5, step=0.1)
        freq_card = st.number_input("Frequência Cardíaca (bpm)", 30, 250, 80)
        freq_resp = st.number_input("Frequência Respiratória (rpm)", 5, 60, 16)
    with col2:
        pressao_s = st.number_input("Pressão Sistólica (mmHg)", 50, 250, 120)
        pressao_d = st.number_input("Pressão Diastólica (mmHg)", 30, 150, 80)
        spo2 = st.number_input("Saturação O2 (%)", 50, 100, 98)

    nivel_dor = st.slider("Nível de Dor (0 = sem dor, 10 = dor máxima)", 0, 10, 0)

    st.divider()

    # Sintomas por região
    st.markdown("### 🩺 Sintomas")

    regioes = {
        "Cabeça": ["cc_headache", "cc_dizziness", "cc_confusion", "cc_lossofconsciousness"],
        "Tórax": ["cc_chestpain", "cc_shortnessofbreath", "cc_palpitations", "cc_respiratorydistress"],
        "Abdômen": ["cc_abdominalpain", "cc_nausea", "cc_emesis", "cc_diarrhea"],
        "Geral": ["cc_fever", "cc_fatigue", "cc_weakness", "cc_chills"],
        "Membros": ["cc_legpain", "cc_legswelling", "cc_armpain", "cc_numbness"],
    }

    nomes_amigaveis = {
        "cc_headache": "Dor de cabeça",
        "cc_dizziness": "Tontura",
        "cc_confusion": "Confusão mental",
        "cc_lossofconsciousness": "Perda de consciência",
        "cc_chestpain": "Dor no peito",
        "cc_shortnessofbreath": "Falta de ar",
        "cc_palpitations": "Palpitações",
        "cc_respiratorydistress": "Dificuldade respiratória",
        "cc_abdominalpain": "Dor abdominal",
        "cc_nausea": "Náusea",
        "cc_emesis": "Vômito",
        "cc_diarrhea": "Diarreia",
        "cc_fever": "Febre",
        "cc_fatigue": "Fadiga",
        "cc_weakness": "Fraqueza",
        "cc_chills": "Calafrios",
        "cc_legpain": "Dor nas pernas",
        "cc_legswelling": "Inchaço nas pernas",
        "cc_armpain": "Dor nos braços",
        "cc_numbness": "Dormência",
    }

    sintomas_selecionados = {}
    for regiao, cols in regioes.items():
        with st.expander(f"📍 {regiao}"):
            for col in cols:
                sintomas_selecionados[col] = 1 if st.checkbox(nomes_amigaveis[col], key=col) else 0

    if st.button("Ver Resultado →", type="primary"):
        # Monta dados para o modelo
        dados = st.session_state.dados_triagem.copy()
        dados.update({
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
        })

        # Adiciona laboratorio com zeros (não coletado na triagem)
        labs = [
            'wbc_last','hemoglobin_last','platelets_last','sodium_last',
            'potassium_last','creatinine_last','glucose_last','bun_last',
            'co2_last','lactate,poc_last','troponint_last','inr_last'
        ]
        for lab in labs:
            dados[lab] = 0

        # Adiciona histórico
        dados["n_edvisits"] = 0
        dados["n_admissions"] = 0

        # Adiciona sintomas
        dados.update(sintomas_selecionados)

        # Preenche colunas faltantes com 0
        colunas_modelo = modelo.feature_names_in_
        entrada = {col: dados.get(col, 0) for col in colunas_modelo}
        df_entrada = pd.DataFrame([entrada])

        resultado = modelo.predict(df_entrada)[0]
        proba = modelo.predict_proba(df_entrada)[0]

        # Salva no banco
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO triagens (paciente_id, temperatura, pressao_sistol, pressao_diast,
                freq_cardiaca, nivel_dor, nivel_risco, descricao_risco, cor_risco)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            st.session_state.paciente_id,
            temp, pressao_s, pressao_d, freq_card, nivel_dor,
            int(resultado),
            ["Não urgente","Pouco urgente","Urgente","Emergência","Emergência imediata"][resultado-1],
            ["verde","amarelo","laranja","vermelho","vermelho"][resultado-1]
        ))
        conn.commit()
        conn.close()

        st.session_state.dados_triagem["resultado"] = int(resultado)
        st.session_state.dados_triagem["proba"] = proba.tolist()
        st.session_state.pagina = 3
        st.rerun()

    if st.button("← Voltar"):
        st.session_state.pagina = 1
        st.rerun()

# ── PÁGINA 3: RESULTADO ─────────────────────────────────────────────
elif st.session_state.pagina == 3:
    st.title("🏥 Sistema de Triagem Hospitalar")
    st.subheader("Passo 3 — Resultado da Triagem")
    st.divider()

    resultado = st.session_state.dados_triagem["resultado"]

    cores = {1: "🟢", 2: "🟡", 3: "🟠", 4: "🔴", 5: "🔴"}
    nomes = {1: "Não Urgente", 2: "Pouco Urgente", 3: "Urgente", 4: "Emergência", 5: "Emergência Imediata"}
    tempos = {1: "Pode aguardar", 2: "Atender em até 60 min", 3: "Atender em até 30 min", 4: "Atender em até 10 min", 5: "Atendimento IMEDIATO"}

    emoji = cores[resultado]
    nome = nomes[resultado]
    tempo = tempos[resultado]

    st.markdown(f"## {emoji} ESI {resultado} — {nome}")
    st.markdown(f"**⏱ Prioridade:** {tempo}")
    st.divider()
    st.caption("⚠️ Este resultado é uma sugestão de apoio à decisão clínica. A avaliação final é responsabilidade do profissional de saúde.")

    if st.button("Nova Triagem", type="primary"):
        st.session_state.pagina = 1
        st.session_state.paciente_id = None
        st.session_state.dados_triagem = {}
        st.rerun()