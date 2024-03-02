from asgiref.wsgi import WsgiToAsgi
from botocore.exceptions import ClientError
from discord_interactions import verify_key_decorator
from flask import Flask, jsonify, request
from mangum import Mangum
import boto3
import datetime
import httpx
import json
import boto3


def get_secrets(secret_name="DonaldDiscord", region_name="us-east-1"):
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e
    secret = get_secret_value_response['SecretString']
    return json.loads(secret)

SECRETS = get_secrets()
DISCORD_PUBLIC_KEY = SECRETS["DISCORD_PUBLIC_KEY"]
DISCORD_BOT_TOKEN = SECRETS["DISCORD_BOT_TOKEN"]
print("KEY", DISCORD_PUBLIC_KEY)
print("TOKEN", DISCORD_BOT_TOKEN)

BASE_URL = f"https://discord.com/api/v10"

LEETCODE_CHANNEL_ID = 1194137256898863277
LEETCODE_DOMAIN = "https://leetcode.com"
POTD_QUERY = """query questionOfToday {
	activeDailyCodingChallengeQuestion {
		date
		link
		question {
			difficulty
			title
            frontendQuestionId: questionFrontendId
		}
	}
}"""

app = Flask(__name__)
asgi_app = WsgiToAsgi(app)
handler = Mangum(asgi_app)

async def post_potd():
        # {'data': {'activeDailyCodingChallengeQuestion': {'date': '2024-02-29', 'link': '/problems/even-odd-tree/', 'question': {'difficulty': 'Medium', 'title': 'Even Odd Tree', 'frontendQuestionId': '1609'}}}}

        async with httpx.AsyncClient(cookies=httpx.Cookies()) as client:
            response = await client.get("https://leetcode.com")

        # Retrieve the session ID from the cookies
            csrftoken = client.cookies["csrftoken"]
            headers = {
                    "X-Csrftoken": csrftoken,
                    "Referer": "https://leetcode.com/problemset"
                    }
            daily_question_json = (await client.post(
                "https://leetcode.com/graphql",
                headers=headers,
                data={
                    "operationName": "questionOfToday",
                    "query": POTD_QUERY 
                    }
            )).json()

        daily_challenge = daily_question_json['data']['activeDailyCodingChallengeQuestion']
        question = daily_challenge['question']
        date = datetime.datetime(*map(int, daily_challenge['date'].split('-')))
        month = date.strftime('%B')[:3]
        day = date.strftime('%d').lstrip('0')
        url = LEETCODE_DOMAIN + daily_challenge['link']
        qid = question['frontendQuestionId']

        print(month, day,qid, question['title'] ,question['difficulty'], url)
        async with httpx.AsyncClient(cookies=httpx.Cookies()) as client:
            headers = {"Authorization": f"Bot {DISCORD_BOT_TOKEN}", "Content-Type": "application/json"}
            leetcode_channel_response = await client.get(
                    f"{BASE_URL}/channels/{LEETCODE_CHANNEL_ID}",
                    headers=headers
                    )
            tags = leetcode_channel_response.json()["available_tags"]
            potd_tag_id = next(tag["id"] for tag in tags if tag["name"] == "POTD")
            print(potd_tag_id)
            leetcode_channel_response = await client.post(
                    f"{BASE_URL}/channels/{LEETCODE_CHANNEL_ID}/threads",
                    headers=headers,
                    json={
                        "name": f"{month} {day}: {qid}. {question['title']}",
                        "message": {
                            "content": f"{question['difficulty']}: {url}"
                            },
                        "applied_tags": [potd_tag_id]
                        }
                    )
            print(leetcode_channel_response.text)
        print("posted POTD")
        


@app.route("/", methods=["POST"])
async def interactions():
    print(f"👉 Request: {request.json}")
    raw_request = request.json
    return await interact(raw_request)


@verify_key_decorator(DISCORD_PUBLIC_KEY)
async def interact(raw_request):
    data = raw_request["data"]
    command_name = data["name"]

    if command_name == "potd":
        await post_potd()

    return {"type": 4}

if __name__ == "__main__":
    app.run(debug=True)
