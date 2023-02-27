from datetime import date, datetime, timedelta, timezone
import logging
import os
import time
import pytz
import boto3

logger = logging.getLogger()

TIME_ZONE = pytz.timezone("America/New_York")
DATETIME_NOW = datetime.now(TIME_ZONE)
DATE_TODAY = DATETIME_NOW.date()
# DATE_TODAY = date.today()


def validate_slots(slots):
    if slots["Location"] and slots["Location"]["value"]["originalValue"].lower() not in [
        "new york",
        "ny",
        "log angeles",
        "chicago",
    ]:
        return False, "Location"
    if slots["Cuisine"] and slots["Cuisine"]["value"]["interpretedValue"].lower() not in [
        "taiwanese",
        "chinese",
        "italian",
        "mexican",
        "japanese",
        "indian",
        "korean",
    ]:
        return False, "Cuisine"
    if slots["Date"] and datetime.strptime(slots["Date"]["value"]["interpretedValue"], "%Y-%m-%d").date() < DATE_TODAY:
        print("Date selected:", datetime.strptime(slots["Date"]["value"]["interpretedValue"], "%Y-%m-%d").date())
        print("Date today:", DATE_TODAY)
        return False, "Date"
    if slots["Time"]:
        print("Time selected:", datetime.strptime(slots["Time"]["value"]["interpretedValue"], "%H:%M").time())

    if (
        slots["Date"]
        and slots["Time"]
        and datetime.strptime(slots["Date"]["value"]["interpretedValue"], "%Y-%m-%d").date() == DATE_TODAY
        and datetime.strptime(slots["Time"]["value"]["interpretedValue"], "%H:%M").time() <= DATETIME_NOW.time()
    ):
        return False, "Time"

    return True, None


def delegate(event):
    return {
        "sessionState": {
            # "sessionAttributes": event["sessionState"]["sessionAttributes"],
            "dialogAction": {
                "type": "Delegate",
            },
            "intent": event["sessionState"]["intent"],
        }
    }


def elicit_slot(event, slot_to_elicit):
    return {
        "sessionState": {
            "dialogAction": {
                "type": "ElicitSlot",
                "slotToElicit": slot_to_elicit,
            },
            "intent": event["sessionState"]["intent"],
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": f"Invalid {slot_to_elicit}. Please try again.",
            }
        ],
    }


def lambda_handler(event, context):
    # os.environ["TZ"] = "America/New_York"
    # time.tzset()
    print("event")
    print(event)
    event["slots"] = event["interpretations"][0]["intent"]["slots"]
    print("event.slots")
    print(event["slots"])
    if event["invocationSource"] == "DialogCodeHook":
        is_valid, invalid_slot = validate_slots(event["slots"])
        if not is_valid:
            return elicit_slot(event, invalid_slot)
    elif event["invocationSource"] == "FulfillmentCodeHook":
        print("FulfillmentCodeHook")
        sqs = boto3.client("sqs")
        sqs.send_message(
            QueueUrl="https://sqs.us-east-1.amazonaws.com/010436642224/DiningConciergeQueue",
            MessageBody="Dining suggestion request from LF1",
            MessageAttributes={
                "Location": {
                    "StringValue": event["slots"]["Location"]["value"]["interpretedValue"],
                    "DataType": "String",
                },
                "Cuisine": {
                    "StringValue": event["slots"]["Cuisine"]["value"]["interpretedValue"],
                    "DataType": "String",
                },
                "Date": {
                    "StringValue": event["slots"]["Date"]["value"]["interpretedValue"],
                    "DataType": "String",
                },
                "Time": {
                    "StringValue": event["slots"]["Time"]["value"]["interpretedValue"],
                    "DataType": "String",
                },
                "Phone_number": {
                    "StringValue": event["slots"]["Phone_number"]["value"]["interpretedValue"],
                    "DataType": "String",
                },
                "Number_of_people": {
                    "StringValue": event["slots"]["Number_of_people"]["value"]["interpretedValue"],
                    "DataType": "String",
                },
                "Email": {
                    "StringValue": event["slots"]["Email"]["value"]["interpretedValue"],
                    "DataType": "String",
                },
            },
        )
        return {
            "sessionState": {
                "dialogAction": {"type": "Close"},
                "intent": {
                    "confirmationState": "Confirmed",
                    "name": "DiningSuggestionsIntent",
                    "state": "Fulfilled",
                },
            },
            "messages": [
                {
                    "contentType": "PlainText",
                    "content": "Thanks, everything looks good! I'll be texting you the restaurant suggestions to your number shortly.",
                }
            ],
        }
    return delegate(event)
