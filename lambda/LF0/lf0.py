import boto3
import json

# Define the client to interact with Lex
client = boto3.client("lexv2-runtime")


def lambda_handler(event, context):
    print(event)
    print({"loaded_body": json.loads(event["body"])})
    msg_from_user = json.loads(event["body"])["messages"][0]["unstructured"]["text"]
    # msg_from_user = "place to eat"
    # change this to the message that user submits on
    # your website using the 'event' variable
    # msg_from_user = "Hello"
    print(f"Message from frontend: {msg_from_user}")
    # Initiate conversation with Lex
    response = client.recognize_text(
        botId="ZIZBH9YJTQ",  # MODIFY HERE
        botAliasId="EYXMFEHTOW",  # MODIFY HERE
        localeId="en_US",
        sessionId="testuser",
        text=msg_from_user,
    )

    msg_from_lex = response.get("messages", [])
    print("all messages from lex")
    print(msg_from_lex)
    if msg_from_lex:
        print(f"Message from Chatbot: {msg_from_lex[0]['content']}")
        print(response)
        intent_type = response["sessionState"]["intent"]["name"]
        resp = None
        if intent_type == "GreetingIntent" or intent_type == "ThankYouIntent" or intent_type == "DiningSuggestionsIntent":
            resp = {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
                },
                "body": json.dumps(
                    {"messages": [{"type": "unstructured", "unstructured": {"text": msg_from_lex[0]["content"]}}]}
                ),
            }
        # elif intent_type == 'ThankYouIntent':
        # modify resp to send back the next question Lex would ask from the user

        # format resp in a way that is understood by the frontend
        # HINT: refer to function insertMessage() in chat.js that you uploaded
        # to the S3 bucket
        return resp
