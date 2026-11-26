from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, DoubleType, IntegerType

spark = SparkSession.builder.appName("fraud-stream").master("local[2]").getOrCreate()
spark.sparkContext.setLogLevel("WARN")

# Schéma imposé : les colonnes attendues et leur type
champs = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount", "Class"]
schema = StructType([StructField("transaction_id", IntegerType())]
                    + [StructField(c, DoubleType()) for c in champs])

# Lecture continue du topic Kafka
brut = (spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", "localhost:9092")
        .option("subscribe", "transactions")
        .option("startingOffsets", "earliest")
        .load())

# Conversion du JSON en colonnes
transactions = (brut.select(from_json(col("value").cast("string"), schema).alias("t"))
                .select("t.*"))

# Validation : on rejette les messages mal formés (identifiant absent)
valides = transactions.filter(col("transaction_id").isNotNull())

query = (valides.select("transaction_id", "Time", "Amount", "Class")
         .writeStream.format("console")
         .option("numRows", 10)
         .option("truncate", False)
         .start())
query.awaitTermination()
