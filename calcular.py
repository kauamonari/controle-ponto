from collections import defaultdict
from datetime import datetime

registros = [
    # cole aqui sua lista
]

dias = defaultdict(list)

for r in registros:
    dias[r["data"]].append(r["hora"])

for data, horarios in dias.items():

    horarios.sort()

    if len(horarios) == 4:

        entrada = horarios[0]
        almoco_saida = horarios[1]
        almoco_volta = horarios[2]
        saida = horarios[3]

        fmt = "%H:%M:%S"

        horas_trabalhadas = (
            datetime.strptime(saida, fmt)
            - datetime.strptime(entrada, fmt)
        )

        almoco = (
            datetime.strptime(almoco_volta, fmt)
            - datetime.strptime(almoco_saida, fmt)
        )

        total = horas_trabalhadas - almoco

        print(
            data,
            entrada,
            almoco_saida,
            almoco_volta,
            saida,
            total
        )