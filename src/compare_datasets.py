#!/usr/bin/env python3
"""
Compare les datasets explorés et génère un tableau markdown + JSON.
Usage:
    python src/compare_datasets.py
"""

import json
from pathlib import Path

DOCS = Path("docs/datasets")
CAPTURES = Path("captures")

def load_resume(name: str) -> dict:
    path = DOCS / f"{name}_resume.json"
    if not path.exists():
        raise FileNotFoundError(f"Fichier manquant : {path}")
    with open(path) as f:
        return json.load(f)

def main():
    datasets = {}
    for name in ["ulb", "handbook"]:
        try:
            datasets[name] = load_resume(name)
        except FileNotFoundError as e:
            print(f"⚠ {e}")
            continue

    if not datasets:
        print("Aucun résumé trouvé. Lance d'abord explore_dataset.py")
        return

    # Tableau markdown
    lines = [
        "| Dataset | Lignes | Fraudes | Taux fraude | Colonnes | Montant médian normal | Montant médian fraude | Durée (h) | Valeurs manquantes | Doublons |",
        "|---------|--------|---------|-------------|----------|-----------------------|-----------------------|-----------|--------------------|----------|"
    ]

    for name, d in datasets.items():
        lines.append(
            f"| {d['dataset']} | {d['lignes']:,} | {d['fraudes']:,} | {d['taux_fraude_pourcent']:.4f} % "
            f"| {d['colonnes']} | {d.get('montant_median_normal', '–')} | {d.get('montant_median_fraude', '–')} "
            f"| {d.get('duree_heures', '–')} | {d['valeurs_manquantes']} | {d['lignes_dupliquees']} |"
        )

    md = "\n".join(lines)
    print("\n=== Tableau de comparaison ===\n")
    print(md)

    # Sauvegarde
    out_md = DOCS / "comparaison_datasets.md"
    out_md.write_text(md + "\n", encoding="utf-8")
    print(f"\nTableau sauvegardé → {out_md}")

    # JSON global
    out_json = DOCS / "comparaison_datasets.json"
    with open(out_json, "w") as f:
        json.dump(datasets, f, indent=2, ensure_ascii=False)
    print(f"JSON sauvegardé   → {out_json}")

    # Recommandation automatique
    print("\n=== Recommandation ===")
    print("• ULB          → entraînement + comparaison de modèles (variables déjà prêtes, fort déséquilibre classique)")
    print("• Handbook     → test de volume + règles d'alerte (identifiants, scénarios de fraude, durée longue)")
    print("• PaySim       → optionnel (trop de colonnes de soldes à exclure)")

if __name__ == "__main__":
    main()
