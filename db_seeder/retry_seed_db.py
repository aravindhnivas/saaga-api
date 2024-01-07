from seed_db import safe_post_request

lines = [
    {
        "meta": 2,
        "cat_file": open("seed_files/c038002.cat", "rb"),
        "qn_label_str": "N,Ka,Kc,v",
        "contains_rovibrational": True,
        "vib_qn": "v",
        "notes": "",
    },
    {
        "meta": 4,
        "cat_file": open("seed_files/c039001.cat", "rb"),
        "qn_label_str": "N,Ka,Kc",
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
