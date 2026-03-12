import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def graph(courses, labels, label, img):
    df = pd.DataFrame({'courses':courses, 'labels':labels})

    fig, ax = plt.subplots()

    colors = ['#4E79A7','#F28E2B','#E15759','#76B7B2']

    wedges, _ = ax.pie(
        df.courses,
        colors=colors,
        startangle=90
    )

    cards = []
    for i in range(len(labels)):
        text = f"{labels[i]}: {courses[i]} %"
        patch = mpatches.Patch(color=colors[i], label=text)
        cards.append(patch)

    # LEYENDA
    ax.legend(
        handles=cards,
        loc='upper center',
        bbox_to_anchor=(0.5, 1.05),
        ncol=4,
        frameon=True
    )

    # TITULO (más arriba)
    plt.title(
        label,
        pad=40
    )

    plt.savefig(img, dpi=300, bbox_inches="tight")
    # plt.show()

courses = [97.56, 1.13, 1.20, 0.11]
labels = ['A','B','C','BICI']

graph(
    courses,
    labels,
    "Peak Hour Demand: 08:15 – 09:15 Hrs\nTotal Vehicles: 2744",
    "1.png"
)

courses = [97.63, 1.24, 1.09, 0.04]
labels = ['A','B','C','BICI']

# Período: 12:00 a 15:00 hrs.
# Hora de Máxima Demanda: 12:30 a 13:30 Hrs.
# TOTAL DE VEHICULOS DE MÁXIMA DEMANDA: 2744 VEH.
# A: 97.63 %
# B: 1.24 %
# C: 1.09 %
# BICI: 0.04 %


graph(
    courses,
    labels,
    "Peak Hour Demand: 12:30 – 13:30 Hrs\nTotal Vehicles: 2744",
    "2.png"
)

courses = [97.88, 0.97, 1.12, 0.03]
labels = ['A','B','C','BICI']

# Período: 17:00 a 20:00 hrs.
# Hora de Máxima Demanda: 17:30 a 18:30 Hrs.
# TOTAL DE VEHICULOS DE MÁXIMA DEMANDA: 3391 VEH.
# A: 97.88 %
# B: 0.97 %
# C: 1.12 %
# BICI: 0.03 %


graph(
    courses,
    labels,
    "Peak Hour Demand: 17:30 – 18:30 Hrs\nTotal Vehicles: 3391",
    "3.png"
)

