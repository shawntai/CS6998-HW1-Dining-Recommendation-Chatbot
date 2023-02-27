import boto3
import os
import pandas as pd
import requests
from dotenv import load_dotenv
import datetime
import json

load_dotenv()

API_KEY = os.getenv("YELP_API_KEY")
YELP_API_URL = "https://api.yelp.com/v3/businesses/search"
LOCATION = "Manhattan"

headers = {"Authorization": f"Bearer {API_KEY}"}


df = pd.DataFrame()

cuisines = ["italian", "chinese", "japanese", "korean", "indian"]

for cuisine in cuisines:
    for offset in range(0, 1000, 50):
        params = {"term": "restaurants", "location": LOCATION, "categories": cuisine, "limit": 50, "offset": offset}
        response = requests.get(YELP_API_URL, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            df = pd.concat(
                [
                    df,
                    pd.DataFrame(
                        [
                            {
                                "id": business["id"],
                                "name": business["name"],
                                "address": ", ".join(business["location"]["display_address"]),
                                "zip_code": business["location"]["zip_code"],
                                "latitude": business["coordinates"]["latitude"],
                                "longitude": business["coordinates"]["longitude"],
                                "rating": business["rating"],
                                "review_count": business["review_count"],
                                "cuisine": cuisine,
                            }
                            for business in data["businesses"]
                        ]
                    ),
                ],
                ignore_index=True,
            )
            """
            for business in data["businesses"]:
                df = pd.concat(
                    [
                        df,
                        pd.DataFrame(
                            [
                                {
                                    "id": business["id"],
                                    "name": business["name"],
                                    "address": ", ".join(business["location"]["display_address"]),
                                    "zip_code": business["location"]["zip_code"],
                                    "latitude": business["coordinates"]["latitude"],
                                    "longitude": business["coordinates"]["longitude"],
                                    "rating": business["rating"],
                                    "review_count": business["review_count"],
                                    "cuisine": cuisine,
                                }
                            ]
                        ),
                    ],
                    ignore_index=True,
                )
            """
        else:
            print(f"Error {response.status_code}: {response.reason}")
            break

df.drop_duplicates(subset="id").to_csv("./yelp/yelp-restaurants.csv")


############################################################################################################


# upload to dynamodb
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
    restaurant["insertedAtTimestamp"] = str(datetime.now())
    response = table.put_item(Item=json.loads(json.dumps(restaurant), parse_float=Decimal))


############################################################################################################


# convert to opensearch format
records = df.to_dict("records")

# Initialize an empty list for storing NDJSON data
ndjson_data = []

# Loop through each record and add metadata line and JSON string
for record in records:
    # Create metadata line with index and ID
    meta = {"index": {"_index": "restaurants", "_id": record["id"]}}
    # Serialize metadata line and record into JSON strings
    meta_str = json.dumps(meta)
    record_str = json.dumps({"id": record["id"], "cuisine": record["cuisine"]})
    # Append JSON strings to NDJSON data list, separated by newlines
    ndjson_data.append(meta_str + "\n" + record_str + "\n")

# End request body with a newline character
ndjson_data.append("\n")

# Join NDJSON data list into a single string
request_body = "".join(ndjson_data)

# Save JSON string as a text file
with open("data.json", "w") as f:
    f.write(request_body)
