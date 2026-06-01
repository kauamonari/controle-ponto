import sqlite3

conn = sqlite3.connect("pontos.db")

cursor = conn.cursor()

cursor.execute("""
    SELECT
        periodo,
        data,
        entrada,
        saida,
        saldo
    FROM pontos
""")

dados = cursor.fetchall()

for linha in dados:
    print(linha)

conn.close()