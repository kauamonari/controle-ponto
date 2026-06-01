import re
import base64
from collections import defaultdict
from datetime import datetime
from database import criar_tabelas, limpar_pontos, salvar_ponto
from bs4 import BeautifulSoup
from gmail_reader import conectar_gmail
from excel_export import gerar_excel
from datetime import datetime, timedelta

JORNADA_MINUTOS = 8 * 60 + 48


def ajustar_fechamento(fechamento):
    # 0 = segunda
    # 5 = sábado
    # 6 = domingo

    while fechamento.weekday() in [0, 5, 6]:
        fechamento -= timedelta(days=1)

    return fechamento


def obter_fechamento_mes(ano, mes):
    return ajustar_fechamento(
        datetime(ano, mes, 20)
    )


def proximo_mes(ano, mes):
    if mes == 12:
        return ano + 1, 1

    return ano, mes + 1


def mes_anterior(ano, mes):
    if mes == 1:
        return ano - 1, 12

    return ano, mes - 1


def obter_periodo(data_obj):
    ano = data_obj.year
    mes = data_obj.month

    fechamento_atual = obter_fechamento_mes(
        ano,
        mes
    )

    if data_obj <= fechamento_atual:
        ano_ant, mes_ant = mes_anterior(ano, mes)

        fechamento_anterior = obter_fechamento_mes(
            ano_ant,
            mes_ant
        )

        inicio = fechamento_anterior + timedelta(days=1)
        fim = fechamento_atual

    else:
        ano_prox, mes_prox = proximo_mes(ano, mes)

        fechamento_proximo = obter_fechamento_mes(
            ano_prox,
            mes_prox
        )

        inicio = fechamento_atual + timedelta(days=1)
        fim = fechamento_proximo

    return (
        inicio,
        fim,
        f"{inicio.strftime('%d/%m/%Y')} até {fim.strftime('%d/%m/%Y')}"
    )

service = conectar_gmail()
criar_tabelas()
limpar_pontos()

messages = []
page_token = None

while True:
    results = service.users().messages().list(
        userId="me",
        q="from:rhid.naoresponda@controlid.com.br",
        maxResults=500,
        pageToken=page_token
    ).execute()

    messages.extend(results.get("messages", []))

    page_token = results.get("nextPageToken")

    if not page_token:
        break

print(f"\nTotal de emails encontrados: {len(messages)}\n")

registros = []

for msg_ref in messages:
    try:
        msg = service.users().messages().get(
            userId="me",
            id=msg_ref["id"]
        ).execute()

        payload = msg["payload"]
        html = ""

        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/html":
                    data = part["body"].get("data")

                    if data:
                        html = base64.urlsafe_b64decode(data).decode(
                            "utf-8",
                            errors="ignore"
                        )
        else:
            data = payload["body"].get("data")

            if data:
                html = base64.urlsafe_b64decode(data).decode(
                    "utf-8",
                    errors="ignore"
                )

        if not html:
            continue

        texto = BeautifulSoup(html, "html.parser").get_text(" ")

        match = re.search(
            r"Data e Horário do Registro:\s*(\d{2}/\d{2}/\d{4})\s*(\d{2}:\d{2}:\d{2})",
            texto
        )

        if match:
            registros.append({
                "data": match.group(1),
                "hora": match.group(2)
            })

    except Exception as e:
        print(f"Erro ao processar email: {e}")

dias = defaultdict(list)

for registro in registros:
    dias[registro["data"]].append(registro["hora"])

saldo_total = 0
saldo_periodo = 0
periodo_anterior = None
linhas_excel = []

for data, horarios in sorted(
    dias.items(),
    key=lambda x: datetime.strptime(x[0], "%d/%m/%Y")
):
    data_obj = datetime.strptime(data, "%d/%m/%Y")
    _, _, periodo_atual = obter_periodo(data_obj)

    eh_sabado = data_obj.weekday() == 5

    if periodo_anterior is None:
        periodo_anterior = periodo_atual

        print("\n" + "=" * 100)
        print(f"PERÍODO: {periodo_atual}")
        print("=" * 100)
        print(
            f"{'DATA':12}"
            f"{'ENTRADA':12}"
            f"{'SAÍDA ALM':12}"
            f"{'VOLTA ALM':12}"
            f"{'SAÍDA':12}"
            f"{'TRAB.':12}"
            f"{'SALDO'}"
        )
        print("=" * 100)

    elif periodo_atual != periodo_anterior:
        horas_periodo = int(abs(saldo_periodo) // 60)
        minutos_periodo = int(abs(saldo_periodo) % 60)
        sinal_periodo = "+" if saldo_periodo >= 0 else "-"

        print(
            f"\nSALDO DO PERÍODO {periodo_anterior}: "
            f"{sinal_periodo}{horas_periodo:02d}:{minutos_periodo:02d}"
        )

        saldo_periodo = 0
        periodo_anterior = periodo_atual

        print("\n" + "=" * 100)
        print(f"PERÍODO: {periodo_atual}")
        print("=" * 100)
        print(
            f"{'DATA':12}"
            f"{'ENTRADA':12}"
            f"{'SAÍDA ALM':12}"
            f"{'VOLTA ALM':12}"
            f"{'SAÍDA':12}"
            f"{'TRAB.':12}"
            f"{'SALDO'}"
        )
        print("=" * 100)

    horarios.sort()
    fmt = "%H:%M:%S"

    if eh_sabado and len(horarios) == 2:
        entrada = horarios[0]
        saida = horarios[1]
        saida_almoco = "-"
        volta_almoco = "-"

        trabalhado = (
            datetime.strptime(saida, fmt)
            - datetime.strptime(entrada, fmt)
        )

    elif len(horarios) == 4:
        entrada = horarios[0]
        saida_almoco = horarios[1]
        volta_almoco = horarios[2]
        saida = horarios[3]

        periodo_1 = (
            datetime.strptime(saida_almoco, fmt)
            - datetime.strptime(entrada, fmt)
        )

        periodo_2 = (
            datetime.strptime(saida, fmt)
            - datetime.strptime(volta_almoco, fmt)
        )

        trabalhado = periodo_1 + periodo_2

    else:
        print(f"{data} -> dia incompleto")
        continue

    minutos_trabalhados = trabalhado.total_seconds() / 60

    horas_trabalhadas = int(trabalhado.total_seconds() // 3600)
    minutos_trabalhados_real = int((trabalhado.total_seconds() % 3600) // 60)

    if eh_sabado:
        saldo = minutos_trabalhados
    else:
        saldo = minutos_trabalhados - JORNADA_MINUTOS

    saldo_total += saldo
    saldo_periodo += saldo

    horas_saldo = int(abs(saldo) // 60)
    minutos_saldo = int(abs(saldo) % 60)

    sinal = "+" if saldo >= 0 else "-"

    print(
        f"{data:12}"
        f"{entrada:12}"
        f"{saida_almoco:12}"
        f"{volta_almoco:12}"
        f"{saida:12}"
        f"{horas_trabalhadas:02d}:{minutos_trabalhados_real:02d}       "
        f"{sinal}{horas_saldo:02d}:{minutos_saldo:02d}"
    )

    linhas_excel.append([
        periodo_atual,
        data,
        entrada,
        saida_almoco,
        volta_almoco,
        saida,
        f"{horas_trabalhadas:02d}:{minutos_trabalhados_real:02d}",
        f"{sinal}{horas_saldo:02d}:{minutos_saldo:02d}"
    ])

    salvar_ponto(
    periodo_atual,
    data,
    entrada,
    saida_almoco,
    volta_almoco,
    saida,
    f"{horas_trabalhadas:02d}:{minutos_trabalhados_real:02d}",
    f"{sinal}{horas_saldo:02d}:{minutos_saldo:02d}"
)

if periodo_anterior is not None:
    horas_periodo = int(abs(saldo_periodo) // 60)
    minutos_periodo = int(abs(saldo_periodo) % 60)
    sinal_periodo = "+" if saldo_periodo >= 0 else "-"

    print(
        f"\nSALDO DO PERÍODO {periodo_anterior}: "
        f"{sinal_periodo}{horas_periodo:02d}:{minutos_periodo:02d}"
    )

horas_total = int(abs(saldo_total) // 60)
minutos_total = int(abs(saldo_total) % 60)
sinal_total = "+" if saldo_total >= 0 else "-"

print("\n" + "=" * 100)
print(
    f"SALDO ACUMULADO GERAL: "
    f"{sinal_total}{horas_total:02d}:{minutos_total:02d}"
)
print("=" * 100)

gerar_excel(
    linhas_excel,
    f"{sinal_total}{horas_total:02d}:{minutos_total:02d}"
)