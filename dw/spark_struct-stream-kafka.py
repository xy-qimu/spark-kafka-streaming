from pyspark.sql import SparkSession
from pyspark.sql.types import *
import pyspark.sql.functions as F

spark = SparkSession \
    .builder \
    .appName("kafka-streaming") \
    .getOrCreate()

# 从kafka topic获取数据
kStream_DF = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "dbserver1.inventory.customers") \
    .option("startingOffsets", "earliest") \
    .load()

# kafka二进制数据转成字符串
kStreamStr_DF = kStream_DF.selectExpr("cast(key as STRING) as key", "cast(value as STRING) as value")

# topic schema
topic_fields = StructType([
     StructField('id', StringType(), True),
     StructField('first_name', StringType(), True),
     StructField('last_name', StringType(), True),
     StructField('email', StringType(), True)
     ]
)

# 解析topic中的json 数据
res_DF = kStreamStr_DF \
    .withColumn("payload_after", F.get_json_object(F.col("value"), "$.payload.after")) \
    .withColumn("message", F.from_json(F.col("payload_after"), topic_fields)) \
    .select(*[F.col("message").getItem(f).alias(f) for f in topic_fields.names]) \
    .groupby("first_name").count()

# 启动 stream 并输出
res_DF.writeStream \
    .outputMode("complete") \
    .format("console") \
    .option("truncate", "false") \
    .start() \
    .awaitTermination()
