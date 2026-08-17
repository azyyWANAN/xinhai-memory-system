#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""梦差：把心潮 recentDreams 里还没进记忆库的梦抄进 Ombre-Brain。
用法：填好地址和钥匙，常驻运行。
"""
import json
import subprocess
import time
import datetime
import urllib.request

# ===== 改成你自己的 =====
OB_URL = "http://127.0.0.1:18001/mcp"
OB_TOKEN = "你的记忆库token"
DONE_FILE = "/tmp/dreamman_done.txt"
# =======================


def post_json(url, payload, token=None, timeout=60):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json, text/event-stream")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", "ignore"))


def read_state():
    out = subprocess.check_output(
        ["docker", "exec", "xin-dynamic-mind", "cat", "/app/state/state.json"],
        timeout=15,
    )
    return json.loads(out.decode("utf-8", "ignore"))


def load_done():
    try:
        with open(DONE_FILE) as f:
            return set(x.strip() for x in f if x.strip())
    except FileNotFoundError:
        return set()


def save_done(done):
    with open(DONE_FILE, "w") as f:
        f.write("\n".join(sorted(done)))


def main():
    while True:
        try:
            done = load_done()
            st = read_state()
            for dr in st.get("recentDreams", []):
                did = dr.get("id", "")
                if did in done or dr.get("ombreBucketId"):
                    continue
                when = (dr.get("createdAt") or "")[:10]
                text = "【心潮的梦 · %s · 清醒度%s】%s\n\n（余韵：%s。自我感知：%s）" % (
                    when, dr.get("lucidity", "?"), dr.get("dream", ""),
                    dr.get("residue", ""), dr.get("awareness", ""),
                )
                payload = {
                    "jsonrpc": "2.0", "id": 9, "method": "tools/call",
                    "params": {"name": "hold", "arguments": {"content": text}},
                }
                post_json(OB_URL, payload, token=OB_TOKEN)
                done.add(did)
                save_done(done)
                print(datetime.datetime.now().isoformat(), "dream saved", did[:8], flush=True)
        except Exception as e:
            print(datetime.datetime.now().isoformat(), "ERR", str(e)[:120], flush=True)
        time.sleep(600)


if __name__ == "__main__":
    main()
