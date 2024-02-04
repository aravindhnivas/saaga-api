from seed_db import safe_post_request
import requests
import os
from dotenv import load_dotenv
import argparse
import json


load_dotenv()

parser = argparse.ArgumentParser(description="Process some integers.")

parser.add_argument(
    "--dev", dest="dev", action="store_true", help="run in development mode"
)

args = parser.parse_args()

domain = os.getenv("DOMAIN" + ("_DEV" if args.dev else ""))
port = os.getenv("PORT" + ("_DEV" if args.dev else ""))
url = f"http://{domain}:{port}"
token_key = os.getenv("TOKEN" + ("_DEV" if args.dev else ""))

TOKEN = None
if token_key:
    TOKEN = f"Token {token_key}"

print(f"{TOKEN=}")


def safe_post_request(endpoint, data, files=None):
    address = f"{url}{endpoint}"
    print(f"Posting to {address=} with {data=}")
    headers = {"Authorization": TOKEN, "accept": "application/json"}
    res = requests.post(address, headers=headers, data=data, files=files)

    if res.ok:
        print(f"Successfully posted to {endpoint=}!")

        data = json.loads(res.text)
        if isinstance(data, dict):
            print(f"returned ID: {data['id']=}\n\n")
            return int(data["id"])
        else:
            return None

    else:
        print(
            f"\nerror code: ({res.status_code}) posting to {endpoint=} with {data=}!\n "
        )
        print(f"{res.text}\nContinuing...\n\n")

    return None

lines = [
    {
        "meta": 4,
        "cat_file": open("seed_files/c037003.cat", "rb"),
        "qn_label_str": "N,Ka,Kc,J+1/2,F",
        "contains_rovibrational": False,
        "vib_qn": "",
        "notes": "",
    },
]


for line in lines:
    line_payload = {k: v for k, v in line.items() if k != "cat_file"}
    safe_post_request(
        "/api/data/line/",
        data=line_payload,
        files={"cat_file": line["cat_file"]},
    )
