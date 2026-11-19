from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("count-check").master("local[2]").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

df = (spark.read.format("kafka")
      .option("kafka.bootstrap.servers", "localhost:9092")
      .option("subscribe", "transactions")
      .option("startingOffsets", "earliest")
      .option("endingOffsets", "latest")
      .load())
print("Messages lus par Spark :", df.count())
