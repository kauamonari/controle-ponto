import sqlite3

DB_NAME = "pontos.db"


def conectar():
    return sqlite3.connect(DB_NAME)


def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pontos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            periodo TEXT NOT NULL,
            data TEXT NOT NULL,
            entrada TEXT,
            saida_almoco TEXT,
            volta_almoco TEXT,
            saida TEXT,
            horas_trabalhadas TEXT,
            saldo TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def limpar_pontos():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM pontos")

    conn.commit()
    conn.close()


def salvar_ponto(
    periodo,
    data,
    entrada,
    saida_almoco,
    volta_almoco,
    saida,
    horas_trabalhadas,
    saldo
):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO pontos (
            periodo,
            data,
            entrada,
            saida_almoco,
            volta_almoco,
            saida,
            horas_trabalhadas,
            saldo
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        periodo,
        data,
        entrada,
        saida_almoco,
        volta_almoco,
        saida,
        horas_trabalhadas,
        saldo
    ))

    conn.commit()
    conn.close()