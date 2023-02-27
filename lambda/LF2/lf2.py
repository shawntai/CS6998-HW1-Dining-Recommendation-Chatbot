# import os
# import boto3
# from dotenv import load_dotenv

# load_dotenv()


# def lambda_handler(event, context):
#     sqs = boto3.client("sqs")
#     response = sqs.receive_messages(
#         QueueUrl=os.getenv("SQS_QUEUE_URL"),
#         MessageAttributeNames=["All"],
#         VisibilityTimeout=0,
#         WaitTimeSeconds=0,
#     )
#     print("sqs response", response)

import json
import os
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from dotenv import load_dotenv
import random

load_dotenv()

REGION = "us-east-1"
HOST = "search-restaurants-ncxb7yzfc5eyanzlpgpwim7f6y.us-east-1.es.amazonaws.com"
INDEX = "restaurants"

sqs = boto3.client("sqs")


def get_restaurant_from_dynamodb(restaurant_id):
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("yelp-restaurants")
    return table.get_item(Key={"id": restaurant_id})["Item"]


def send_email(restaurants, email, cuisine, n_people, date, time):
    ses = boto3.client("ses")
    response = ses.send_email(
        Source="ht2539@columbia.edu",
        Destination={"ToAddresses": [email]},
        Message={
            "Subject": {"Data": "Your restaurant recommendations"},
            "Body": {
                "Text": {
                    "Data": f"""Hello! Here are my {cuisine.capitalize()} restaurant suggestions for {n_people} people, for {date} at {time}:
                    
1. {restaurants[0]['name']}, located at {restaurants[0]['address']}
2. {restaurants[1]['name']}, located at {restaurants[1]['address']}
3. {restaurants[2]['name']}, located at {restaurants[2]['address']}
                    
Enjoy your meal!"""
                }
            },
        },
    )


def lambda_handler(event, context):
    messages = sqs.receive_message(
        QueueUrl=os.getenv("SQS_QUEUE_URL"),
        MessageAttributeNames=["All"],
        VisibilityTimeout=0,
        WaitTimeSeconds=0,
    )
    print("sqs response", messages)
    if not messages or not messages["Messages"]:
        return
    for message in messages["Messages"]:
        cuisine = message["MessageAttributes"]["Cuisine"]["StringValue"]
        n_people = message["MessageAttributes"]["Number_of_people"]["StringValue"]
        date = message["MessageAttributes"]["Date"]["StringValue"]
        time = message["MessageAttributes"]["Time"]["StringValue"]
        phone_number = message["MessageAttributes"]["Phone_number"]["StringValue"]
        email = message["MessageAttributes"]["Email"]["StringValue"]
        results = query(cuisine)
        print("results", results)
        restaurant_ids = random.sample([result["id"] for result in results], 3)
        restaurants = [get_restaurant_from_dynamodb(id) for id in restaurant_ids]
        print("restaurants", restaurants)
        send_email(restaurants, email, cuisine, n_people, date, time)
        sqs.delete_message(
            QueueUrl=os.getenv("SQS_QUEUE_URL"),
            ReceiptHandle=message["ReceiptHandle"],
        )
    return


def query(term):
    q = {"size": 5, "query": {"multi_match": {"query": term}}}
    client = OpenSearch(
        hosts=[{"host": HOST, "port": 443}],
        http_auth=get_awsauth(REGION, "es"),
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
    )
    res = client.search(index=INDEX, body=q)
    print(res)
    hits = res["hits"]["hits"]
    results = []
    for hit in hits:
        results.append(hit["_source"])
    return results


def get_awsauth(region, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key, cred.secret_key, region, service, session_token=cred.token)
