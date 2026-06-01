import sqlite3
from flask import Flask, render_template

app = Flask(__name__)


def saldo_para_minutos(saldo):
    sinal = -1 if saldo.startswith("-") else 1
    horas, minutos = saldo[1:].split(":")
    return sinal * ((int(horas) * 60) + int(minutos))


def minutos_para_saldo(total):
    sinal = "+" if total >= 0 else "-"
    total = abs(total)

    horas = total // 60
    minutos = total % 60

    return f"{sinal}{horas:02d}:{minutos:02d}"


@app.route("/")
def home():
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
        ORDER BY id DESC
    """)

    pontos = cursor.fetchall()

    cursor.execute("""
        SELECT
            periodo,
            saldo
        FROM pontos
    """)

    dados_resumo = cursor.fetchall()

    conn.close()

    resumo_periodos = {}

    for periodo, saldo in dados_resumo:
        resumo_periodos.setdefault(periodo, 0)
        resumo_periodos[periodo] += saldo_para_minutos(saldo)

    cards = []

    for periodo, total_minutos in resumo_periodos.items():
        cards.append({
            "periodo": periodo,
            "saldo": minutos_para_saldo(total_minutos)
        })

    return render_template(
        "index.html",
        pontos=pontos,
        cards=cards
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)