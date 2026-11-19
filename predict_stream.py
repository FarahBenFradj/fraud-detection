import os
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import StructType, StructField, DoubleType, IntegerType
from pyspark.ml.classification import RandomForestClassificationModel
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.functions import vector_to_array

# Le mot de passe vient de l'environnement, jamais écrit dans le code
ES_PASSWORD = os.environ["ELASTIC_PASSWORD"]

spark = SparkSession.builder.appName("fraud-predict").master("local[2]").getOrCreate()
spark.sparkContext.setLogLevel("WARN")

champs = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount", "Class"]
schema = StructType([StructField("transaction_id", IntegerType())]
                    + [StructField(c, DoubleType()) for c in champs])

# 1. Lecture du flux Kafka et validation du schéma
brut = (spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", "localhost:9092")
        .option("subscribe", "transactions")
        .option("startingOffsets", "earliest")
        .load())
tx = (brut.select(F.from_json(F.col("value").cast("string"), schema).alias("t"))
      .select("t.*")
      .filter(F.col("transaction_id").isNotNull()))

# 2. Application du modèle entraîné (BF4)
colonnes = [f"V{i}" for i in range(1, 29)] + ["Amount"]
assembler = VectorAssembler(inputCols=colonnes, outputCol="features", handleInvalid="skip")
modele = RandomForestClassificationModel.load("models/rf_avec_ponderation")
pred = modele.transform(assembler.transform(tx))

sortie = (pred.select("transaction_id", "Time", "Amount",
                      F.col("Class").cast("int").alias("classe_reelle"),
                      F.col("prediction").cast("int").alias("prediction"),
                      vector_to_array("probability")[1].alias("score"))
          .withColumn("horodatage", F.current_timestamp()))

# 3. Écriture dans Elasticsearch (BF6), lot par lot
def ecrire_dans_es(lot, id_lot):
    n = lot.count()
    if n == 0:
        return
    (lot.write.format("es")
        .option("es.nodes", "localhost")
        .option("es.port", "9200")
        .option("es.nodes.wan.only", "true")
        .option("es.net.http.auth.user", "elastic")
        .option("es.net.http.auth.pass", ES_PASSWORD)
        .option("es.mapping.id", "transaction_id")
        .mode("append")
        .save("fraud-predictions"))
    print(f"Lot {id_lot} : {n} transactions envoyées à Elasticsearch")

query = (sortie.writeStream
         .foreachBatch(ecrire_dans_es)
         .option("checkpointLocation", "checkpoints/predictions")
         .start())
query.awaitTermination()
