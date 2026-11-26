"""Exploration d'un dataset de fraude : chiffres clés + 2 graphiques.
Usage : python src/explore_dataset.py NOM CHEMIN COLONNE_FRAUDE COLONNE_MONTANT [COLONNE_TEMPS]
"""
import sys, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")           # pas d'écran : on enregistre des images
import matplotlib.pyplot as plt

nom, chemin, col_fraude, col_montant = sys.argv[1:5]
col_temps = sys.argv[5] if len(sys.argv) > 5 else None

df = pd.read_csv(chemin)
n = len(df)
fraude = df[col_fraude] == 1
n_fraudes = int(fraude.sum())

resume = {
    "dataset": nom,
    "lignes": n,
    "colonnes": df.shape[1],
    "fraudes": n_fraudes,
    "taux_fraude_pourcent": round(n_fraudes / n * 100, 4),
    "valeurs_manquantes": int(df.isna().sum().sum()),
    "lignes_dupliquees": int(df.duplicated().sum()),
    "montant_median_normal": round(float(df.loc[~fraude, col_montant].median()), 2),
    "montant_median_fraude": round(float(df.loc[fraude, col_montant].median()), 2),
    "montant_max": round(float(df[col_montant].max()), 2),
}
if col_temps:
    resume["duree_heures"] = round(float(df[col_temps].max() - df[col_temps].min()) / 3600, 1)

print("=== Résumé du dataset", nom, "===")
for cle, val in resume.items():
    print(f"{cle:28s} {val}")
print("\nColonnes :", ", ".join(df.columns[:12]), "..." if df.shape[1] > 12 else "")

with open(f"docs/datasets/{nom}_resume.json", "w") as f:
    json.dump(resume, f, indent=2, ensure_ascii=False)

# Graphique 1 : déséquilibre des classes (échelle log pour voir les fraudes)
plt.figure(figsize=(5, 4))
plt.bar(["Normales", "Fraudes"], [n - n_fraudes, n_fraudes], color=["#4c78a8", "#e45756"])
plt.yscale("log")
plt.ylabel("Nombre de transactions (échelle log)")
plt.title(f"{nom} : déséquilibre ({resume['taux_fraude_pourcent']} % de fraudes)")
plt.tight_layout()
plt.savefig(f"captures/P4-{nom}-desequilibre.png", dpi=150)
plt.close()

# Graphique 2 : distribution des montants, fraudes contre normales
plt.figure(figsize=(6, 4))
plt.hist(np.log10(df.loc[~fraude, col_montant] + 1), bins=50, alpha=0.6, density=True, label="Normales")
plt.hist(np.log10(df.loc[fraude, col_montant] + 1), bins=50, alpha=0.6, density=True, label="Fraudes")
plt.xlabel("log10(montant + 1)")
plt.ylabel("Densité")
plt.title(f"{nom} : montants")
plt.legend()
plt.tight_layout()
plt.savefig(f"captures/P4-{nom}-montants.png", dpi=150)
plt.close()
print("\nGraphiques enregistrés dans captures/")
