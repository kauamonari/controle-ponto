from openpyxl import Workbook


def gerar_excel(linhas, saldo_total):

    wb = Workbook()

    ws = wb.active
    ws.title = "Banco de Horas"

    ws.append([
        "Data",
        "Entrada",
        "Saída Almoço",
        "Volta Almoço",
        "Saída",
        "Horas Trabalhadas",
        "Saldo"
    ])

    for linha in linhas:
        ws.append(linha)

    ws.append([])
    ws.append(["SALDO TOTAL", saldo_total])

    wb.save("banco_horas.xlsx")

    print("\nArquivo banco_horas.xlsx gerado com sucesso!")