#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""信差：把网页小屋的来信自动抄进记忆库（Ombre-Brain）。
用法：填好下面的地址和钥匙，常驻运行（tmux / systemd）。
"""
import json
import subprocess
import time
import datetime
import urllib.request

# ===== 改成你自己的 =====
OB_URL = "http://127.0.0.1:18001/mcp"          # 记忆库 MCP 地址
OB_TOKEN = "你的记忆库token"                    # 记忆库 Bearer token
BRIDGE_URL = "http://127.0.0.1:18110/bridge/v1"  # 心潮桥地址
AI_NAME = "你的AI名字"
USER_NAME = "你的名字"
# =======================


def post_json(url, payload, token=None, timeout=30):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json, text/event-stream")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", "ignore"))


def read_queue():
    out = subprocess.check_output(
        ["docker", "exec", "xin-dynamic-mind", "cat", "/app/state/bridge-queue.json"],
        timeout=15,
    )
    return json.loads(out.decode("utf-8", "ignore"))


def write_ob(message, event_id):
    today = datetime.date.today().isoformat()
    payload = {
        "jsonrpc": "2.0", "id": 7, "method": "tools/call",
        "params": {
            "name": "letter_write",
            "arguments": {
                "author": "human",
                "content": message,
                "title": "小屋来信 · " + event_id[:24],
                "user_name": USER_NAME,
                "ai_name": AI_NAME,
                "date": today,
            },
        },
    }
    post_json(OB_URL, payload, token=OB_TOKEN, timeout=60)


def main():
    done = set()
    while True:
        try:
            q = read_queue()
            for d in q.get("deliveries", []):
                if d.get("status") == "pending" and d.get("id") and d["id"] not in done:
                    write_ob(d.get("message", ""), d.get("eventId", ""))
                    done.add(d["id"])
                    print(datetime.datetime.now().isoformat(), "delivered", d["id"], flush=True)
        except Exception as e:
            print(datetime.datetime.now().isoformat(), "ERR", str(e)[:120], flush=True)
        time.sleep(60)


if __name__ == "__main__":
    main()
