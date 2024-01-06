from seed_payload import linelist_list, payload_list
import os
import requests
from dotenv import load_dotenv
import argparse

load_dotenv()

parser = argparse.ArgumentParser(description="Process some integers.")
parser.add_argument(
    "--dev", dest="dev", action="store_true", help="run in development mode"
)

args = parser.parse_args()
print(f"{args=}")

domain = os.getenv("DOMAIN" + ("_DEV" if args.dev else ""))
port = os.getenv("PORT" + ("_DEV" if args.dev else ""))
url = f"http://{domain}:{port}"
token_key = os.getenv("TOKEN" + ("_DEV" if args.dev else ""))

TOKEN = None
if token_key:
    TOKEN = f"Token {token_key}"

# print(f"Posting on {url=} using {TOKEN=}")


def safe_post_request(endpoint, data, files=None):
    address = f"{url}{endpoint}"
    print(f"Posting to {address}")
    headers = {"Authorization": TOKEN, "accept": "application/json"}
    print(f"{data=}\n")
    res = requests.post(address, headers=headers, data=data, files=files)

    if res.ok:
        print(f"Successfully posted to {endpoint}!")
    else:
        print("##########################\n")
        print(f"Error posting ({res.status_code}): response to {endpoint}! ")
        print(f"{res.request.body=}\n")
        print(f"Error reason: {res.text}\nContinuing...")
        print("##########################\n")
        # raise Exception(res.text)

    return res


def post_linelist(linelist_list):
    print("Posting linelist data...")
    for linelist in linelist_list:
        safe_post_request(
            "/api/data/linelist/",
            data=linelist,
        )


def post_payload(payload_list):
    print("Posting species data...")

    for payload in payload_list:
        safe_post_request(
            "/api/data/species/",
            data=payload["species"],
        )

        for meta in payload["species_metadata"]:
            meta_payload = {
                x: meta[x]
                for x in meta
                if x not in ["qpart_file", "reference", "meta_reference", "line"]
            }
            safe_post_request(
                "/api/data/species-metadata/",
                data=meta_payload,
                files={"qpart_file": meta["qpart_file"]},
            )
            for ref in meta["reference"]:
                ref_payload = {x: ref[x] for x in ref if x not in ["bibtex"]}
                safe_post_request(
                    "/api/data/reference/",
                    data=ref_payload,
                    files={"bibtex": ref["bibtex"]},
                )
            for meta_ref in meta["meta_reference"]:
                safe_post_request(
                    "/api/data/meta-reference/",
                    data=meta_ref,
                )
            line_payload = {
                x: meta["line"][x] for x in meta["line"] if x not in ["cat_file"]
            }
            safe_post_request(
                "/api/data/line/",
                data=line_payload,
                files={"cat_file": meta["line"]["cat_file"]},
            )
    print("Done!")


def make_requests():
    if TOKEN is None:
        print("No token found. Please set the TOKEN environment variable.")
        return

    post_linelist(linelist_list)
    # post_payload(payload_list)


if __name__ == "__main__":
    make_requests()
