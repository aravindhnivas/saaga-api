from seed_payload import linelist_list, payload_list
import os
import requests
from dotenv import load_dotenv
import argparse
from loguru import logger
import json

logger.add("./logs/file_info.log", level="INFO")
logger.add("./logs/file_error.log", level="ERROR")
load_dotenv()

parser = argparse.ArgumentParser(description="Process some integers.")

parser.add_argument(
    "--dev", dest="dev", action="store_true", help="run in development mode"
)

parser.add_argument(
    "-n",
    "--payload_number",
    dest="n",
    type=int,
    default=len(payload_list),
    help="payload number to post",
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
        
        # logger.info(f"Response: {res.text}")
        data = json.loads(res.text)
        logger.info(f"Linelist ID: {data['id']}")
        
        if isinstance(data, dict):
            return int(data['id'])
        else:
            return None
        
    else:
        logger.error(
            f"\nerror code: ({res.status_code}) posting to {endpoint=} with {data=}!\n "
        )
        logger.error(f"{res.text}\nContinuing...\n\n")

    return None


linelist_ids = {}


def post_linelist(linelist_list):
    global linelist_ids
    logger.info("Posting linelist data...")
    
    for i, linelist in enumerate(linelist_list):
        linelist_id = safe_post_request(
            "/api/data/linelist/",
            data=linelist,
        )
        
        linelist_ids[i+1] = linelist_id
        logger.info(f"{i} - Finished posting {linelist} ({linelist_ids[i+1]=})!")
        

def post_payload(payload_list):
    logger.info("Posting species data...")

    for payload in payload_list:
        logger.info(f"Posting {payload['species']['iupac_name']}...")

        species_id = safe_post_request(
            "/api/data/species/",
            data=payload["species"],
        )
        
        if species_id is None:
            logger.error(f"Failed to post {payload['species']['iupac_name']}")
            continue
        

        for meta in payload["species_metadata"]:
            # Posting species metadata
            meta_payload = {
                x: meta[x]
                for x in meta
                if x not in ["qpart_file", "reference", "meta_reference", "line"]
            }
            
            meta_payload["species"] = species_id
            meta_payload["linelist"] = linelist_ids[meta_payload["linelist"]]
            
            meta_id = safe_post_request(
                "/api/data/species-metadata/",
                data=meta_payload,
                files={"qpart_file": meta["qpart_file"]},
            )
            
            if meta_id is None:
                logger.error(f"Failed to post metadata for {payload['species']['iupac_name']}")
                continue

            for ref, meta_ref in zip(meta["reference"], meta["meta_reference"]):
                ref_payload = {x: ref[x] for x in ref if x not in ["bibtex"]}
                ref_id = safe_post_request(
                    "/api/data/reference/",
                    data=ref_payload,
                    files={"bibtex": ref["bibtex"]},
                )
                
                if ref_id is None:
                    logger.error(f"Failed to post meta reference for {payload['species']['iupac_name']}")
                    continue
                
                meta_ref['meta'] = meta_id
                meta_ref['ref'] = ref_id
                
                safe_post_request(
                    "/api/data/meta-reference/",
                    data=meta_ref,
                )

            # Posting line data
            line_payload = {
                x: meta["line"][x] for x in meta["line"] if x not in ["cat_file"]
            }
            
            line_payload['meta'] = meta_id
            safe_post_request(
                "/api/data/line/",
                data=line_payload,
                files={"cat_file": meta["line"]["cat_file"]},
            )

        logger.info(
            f"Finished posting species metadata for {payload['species']['iupac_name']}!"
        )

    logger.info("Done!")


@logger.catch
def make_requests():
    if TOKEN is None:
        logger.error("No token found. Please set the TOKEN environment variable.")
        return

    post_linelist(linelist_list)
    post_payload(payload_list[: args.n])


if __name__ == "__main__":
    # pass
    make_requests()
