import sqlite3
import os

CAMINHO_BANCO = "triagem.db"


def conectar():
    """Retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect(CAMINHO_BANCO)
    conn.row_factory = sqlite3.Row  
    return conn


def inicializar_banco():
    """Cria as tabelas e insere os dados iniciais se ainda não existirem."""
    conn = conectar()
    cursor = conn.cursor()

    # ── Tabela de pacientes ───
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pacientes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nome        TEXT NOT NULL,
            cpf         TEXT UNIQUE NOT NULL,
            data_nasc   TEXT NOT NULL,
            sexo        TEXT CHECK(sexo IN ('M', 'F', 'Outro')),
            telefone    TEXT,
            criado_em   TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # ── Tabela de sintomas por região ────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sintomas (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            regiao  TEXT NOT NULL,
            nome    TEXT NOT NULL
        )
    """)

    # ── Tabela de triagens ───────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS triagens (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id     INTEGER NOT NULL,
            temperatura     REAL,
            pressao_sistol  INTEGER,
            pressao_diast   INTEGER,
            freq_cardiaca   INTEGER,
            nivel_dor       INTEGER CHECK(nivel_dor BETWEEN 0 AND 10),
            nivel_risco     INTEGER,
            descricao_risco TEXT,
            cor_risco       TEXT,
            realizada_em    TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
        )
    """)

    # ── Tabela de relacionamento triagem <-> sintomas ────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS triagem_sintomas (
            triagem_id  INTEGER NOT NULL,
            sintoma_id  INTEGER NOT NULL,
            PRIMARY KEY (triagem_id, sintoma_id),
            FOREIGN KEY (triagem_id) REFERENCES triagens(id),
            FOREIGN KEY (sintoma_id) REFERENCES sintomas(id)
        )
    """)

    # ── Dados iniciais: sintomas por região ──────────────────────────
    # Só insere se a tabela estiver vazia
    cursor.execute("SELECT COUNT(*) FROM sintomas")
    if cursor.fetchone()[0] == 0:
        sintomas = [
            ("Cabeça", "Dor de cabeça"),
            ("Cabeça", "Tontura"),
            ("Cabeça", "Desmaio"),
            ("Cabeça", "Confusão mental"),
            ("Cabeça", "Alteração visual"),
            ("Tórax", "Dor no peito"),
            ("Tórax", "Falta de ar"),
            ("Tórax", "Palpitação"),
            ("Tórax", "Tosse"),
            ("Abdômen", "Dor abdominal"),
            ("Abdômen", "Náusea"),
            ("Abdômen", "Vômito"),
            ("Abdômen", "Diarreia"),
            ("Membros", "Dor nos membros"),
            ("Membros", "Inchaço"),
            ("Membros", "Formigamento"),
            ("Membros", "Fraqueza muscular"),
            ("Geral", "Febre"),
            ("Geral", "Calafrios"),
            ("Geral", "Fadiga intensa"),
            ("Geral", "Perda de consciência"),
        ]
        cursor.executemany(
            "INSERT INTO sintomas (regiao, nome) VALUES (?, ?)", sintomas
        )

    conn.commit()
    conn.close()
    print(f"Banco de dados inicializado em: {os.path.abspath(CAMINHO_BANCO)}")


# ── Executa ao rodar o arquivo diretamente ────
if __name__ == "__main__":
    inicializar_banco()