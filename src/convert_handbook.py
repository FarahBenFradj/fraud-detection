"""Convertit les fichiers .pkl du Handbook en un seul CSV (à faire une seule fois).
Attention : un fichier .pkl peut exécuter du code à l'ouverture.
On ne le fait ici que parce que la source est le dépôt officiel de l'ULB.
"""
import glob
import pandas as pd

fichiers = sorted(glob.glob("data/handbook_raw/data/*.pkl"))
print("Fichiers trouvés :", len(fichiers))
df = pd.concat([pd.read_pickle(f) for f in fichiers], ignore_index=True)
print("Colonnes :", list(df.columns))
print(df.head(3).to_string())
df.to_csv("data/handbook_sim.csv", index=False)
print("Lignes :", len(df), "-> data/handbook_sim.csv")
