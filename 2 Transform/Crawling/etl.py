# Librerias
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

glueContext = GlueContext(SparkContext.getOrCreate())

# catalog: bases de datos y sys nombrees
db_name = "politicians"
tbl_persons = "persons_json"
tbl_membership = "memberships_json"
tbl_organization = "organizations_json"

# Directorios de salida enS3
output_history_dir = "s3://glue-lab-platzi-transformed/legislator_history"
output_lg_single_dir = "s3://glue-lab-platzi-transformed/legislator_single"
output_lg_partitioned_dir = "s3://glue-lab-platzi-transformed/legislator_part"

# Creación de los Dynamic Frames de las tablas de origen
persons = glueContext.create_dynamic_frame.from_catalog(database=db_name, table_name=tbl_persons)
memberships = glueContext.create_dynamic_frame.from_catalog(database=db_name, table_name=tbl_membership)
orgs = glueContext.create_dynamic_frame.from_catalog(database=db_name, table_name=tbl_organization)

# Mantenemos unos campos y se renombran otros
orgs = orgs.drop_fields(['other_names', 'identifiers']).rename_field('id', 'org_id').rename_field('name', 'org_name')

# Union de los frames para crear una historia
l_history = Join.apply(orgs, Join.apply(persons, memberships, 'id', 'person_id'), 'org_id', 'organization_id').drop_fields(['person_id', 'org_id'])

# ---- Escribiendo la salida de la historia ----

# escribiendo el dynamic frame en formato parquet en el directorio "legislator_history" 
glueContext.write_dynamic_frame.from_options(frame = l_history, connection_type = "s3", connection_options = {"path": output_history_dir}, format = "parquet")

# Escribiendo un simple archivo en el directorio "legislator_single"
s_history = l_history.toDF().repartition(1)
s_history.write.parquet(output_lg_single_dir)

# Convirtiendo a dataframe, escribiendo en el directorio "legislator_part"
l_history.toDF().write.parquet(output_lg_partitioned_dir, partitionBy=['org_name'])