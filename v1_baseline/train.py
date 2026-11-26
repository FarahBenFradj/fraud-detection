import json
from pyspark.sql import SparkSession, functions as F
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator

spark = SparkSession.builder.appName("fraud-train").master("local[4]").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

# 1. Lecture du dataset complet (mode batch)
df = (spark.read.csv("data/creditcard.csv", header=True, inferSchema=True)
      .withColumn("label", F.col("Class").cast("double")))

# 2. Séparation dans le temps : 80 % du début pour l'entraînement, 20 % de la fin pour le test
#    (on n'entraîne pas le modèle avec des transactions plus récentes que celles qu'il doit prédire)
seuil = df.approxQuantile("Time", [0.8], 0.001)[0]
train = df.filter(F.col("Time") <= seuil)
test = df.filter(F.col("Time") > seuil)

n_pos = train.filter("label = 1").count()
n_neg = train.filter("label = 0").count()
print(f"Entraînement : {n_neg} normales, {n_pos} fraudes")
print(f"Test : {test.filter('label = 0').count()} normales, {test.filter('label = 1').count()} fraudes")

# 3. Colonnes utilisées par le modèle (on laisse de côté Time)
colonnes = [f"V{i}" for i in range(1, 29)] + ["Amount"]
assembler = VectorAssembler(inputCols=colonnes, outputCol="features")
train_v = assembler.transform(train)
test_v = assembler.transform(test)

# 4. Pondération : chaque fraude pèse autant que le rapport normales / fraudes (BF5)
ratio = n_neg / n_pos
train_v = train_v.withColumn("poids", F.when(F.col("label") == 1, F.lit(ratio)).otherwise(F.lit(1.0)))

# 5. Deux modèles : sans et avec pondération
rf_sans = RandomForestClassifier(featuresCol="features", labelCol="label",
                                 numTrees=50, maxDepth=8, seed=42)
rf_avec = RandomForestClassifier(featuresCol="features", labelCol="label",
                                 numTrees=50, maxDepth=8, seed=42, weightCol="poids")

def evaluer(nom, modele):
    pred = modele.transform(test_v)
    auprc = BinaryClassificationEvaluator(labelCol="label", rawPredictionCol="rawPrediction",
                                          metricName="areaUnderPR").evaluate(pred)
    auroc = BinaryClassificationEvaluator(labelCol="label", rawPredictionCol="rawPrediction",
                                          metricName="areaUnderROC").evaluate(pred)
    tp = pred.filter((F.col("label") == 1) & (F.col("prediction") == 1)).count()
    fp = pred.filter((F.col("label") == 0) & (F.col("prediction") == 1)).count()
    fn = pred.filter((F.col("label") == 1) & (F.col("prediction") == 0)).count()
    tn = pred.filter((F.col("label") == 0) & (F.col("prediction") == 0)).count()
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rappel = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    res = {"modele": nom, "precision": round(precision, 4), "rappel": round(rappel, 4),
           "AUPRC": round(auprc, 4), "AUROC": round(auroc, 4),
           "TP": tp, "FP": fp, "FN": fn, "TN": tn}
    print(res)
    return res

resultats = []
print("Entraînement sans pondération...")
m_sans = rf_sans.fit(train_v)
resultats.append(evaluer("sans_ponderation", m_sans))

print("Entraînement avec pondération...")
m_avec = rf_avec.fit(train_v)
resultats.append(evaluer("avec_ponderation", m_avec))

# 6. Sauvegarde des modèles et des résultats
m_sans.write().overwrite().save("models/rf_sans_ponderation")
m_avec.write().overwrite().save("models/rf_avec_ponderation")
with open("resultats.json", "w") as f:
    json.dump(resultats, f, indent=2, ensure_ascii=False)
print("Terminé. Résultats dans resultats.json")
