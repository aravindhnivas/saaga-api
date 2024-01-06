import sys
from seed_payload import linelist_list, payload_list
import os
import requests
from dotenv import load_dotenv
import argparse
from loguru import logger

logger.add("./logs/file_{time}.log")
load_dotenv()

parser = argparse.ArgumentParser(description="Process some integers.")
parser.add_argument(
    "--dev", dest="dev", action="store_true", help="run in development mode"
)

args = parser.parse_args()
logger.info(f"{args=}")

domain = os.getenv("DOMAIN" + ("_DEV" if args.dev else ""))
port = os.getenv("PORT" + ("_DEV" if args.dev else ""))
url = f"http://{domain}:{port}"
token_key = os.getenv("TOKEN" + ("_DEV" if args.dev else ""))

TOKEN = None
if token_key:
    TOKEN = f"Token {token_key}"


def safe_post_request(endpoint, data, files=None):
    address = f"{url}{endpoint}"
    logger.info(f"Posting to {address=} with {data=}")
    headers = {"Authorization": TOKEN, "accept": "application/json"}
    res = requests.post(address, headers=headers, data=data, files=files)

    if res.ok:
        logger.success(f"Successfully posted to {endpoint=}!\n\n")
    else:
        logger.error(
            f"\nerror code: ({res.status_code}) posting to {endpoint=} with {data=}!\n "
        )
        logger.error(f"{res.text}\nContinuing...\n\n")

    return res


@logger.catch
def post_linelist(linelist_list):
    logger.info("Posting linelist data...")
    for linelist in linelist_list:
        safe_post_request(
            "/api/data/linelist/",
            data=linelist,
        )


def post_payload(payload_list):
    logger.info("Posting species data...")

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
    logger.info("Done!")


@logger.catch
def make_requests():
    if TOKEN is None:
        logger.error("No token found. Please set the TOKEN environment variable.")
        return

    post_linelist(linelist_list)
    post_payload(payload_list)


if __name__ == "__main__":
    make_requests()
