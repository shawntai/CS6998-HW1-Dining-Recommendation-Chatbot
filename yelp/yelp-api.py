import boto3
import os
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("YELP_API_KEY")
YELP_API_URL = "https://api.yelp.com/v3/businesses/search"
LOCATION = "Manhattan"

# params = {"term": "restaurants", "location": "Manhattan", "categories": "italian", "limit": 3}
headers = {"Authorization": f"Bearer {API_KEY}"}
# response = requests.get(url, headers=headers, params=params)

# if response.status_code == 200:
#     data = response.json()
#     print(data)
# else:
#     print(f"Error {response.status_code}: {response.reason}")


df = pd.DataFrame()

cuisines = ["italian", "chinese", "japanese", "korean", "indian"]

# checkpoint

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

# Create a DynamoDB client
# dynamodb = boto3.resource(
#     "dynamodb",
#     aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
#     aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
#     region_name="us-east-1",
# )

# # Get a reference to your table
# table = dynamodb.Table("yelp-restaurants")

# # Define the item to insert
# item = {"id": "123", "name": "John Doe", "email": "john.doe@example.com", "age": 30}

# # Insert the item into the table
# response = table.put_item(Item=item)

# response = table.delete_item(
#     Key={
#         "id": "123",
#     }
# )

# Print the response
# print(response)
