from decimal import Decimal
import json
import os
import boto3
import pandas as pd

df = pd.read_csv("yelp-restaurants.csv", index_col=0)
data = df.to_dict("records")

# Create a DynamoDB client
dynamodb = boto3.resource(
    "dynamodb",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name="us-east-1",
)

# Get a reference to your table
table = dynamodb.Table("yelp-restaurants")

for restaurant in data:
    response = table.put_item(Item=json.loads(json.dumps(restaurant), parse_float=Decimal))

table.get_item(Key={"id": "yelp:restaurant:4bEjOyTaDG24SY5TxsaUNQ"})
# # Define the item to insert
# item = {"id": "123", "name": "John Doe", "email": "john.doe@example.com", "age": 30}

# # Insert the item into the table
# response = table.put_item(Item=item)

# response = table.delete_item(
#     Key={
#         "id": "123",
#     }
# )
