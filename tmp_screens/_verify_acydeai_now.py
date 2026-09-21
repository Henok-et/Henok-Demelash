"""One-shot ACYDEAI tile screenshots (unique filename to avoid races)."""
from __future__ import annotations

import base64
import json
import subprocess
import time
import urllib.request
from pathlib import Path

import websocket

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PORT = 9341
ROOT = Path(r"D:\personal web\Henok Demelash")
OUT = ROOT / "tmp_screens"
UD = OUT / "profile-acydeai-vnow"
UD.mkdir(parents=True, exist_ok=True)

proc = subprocess.Popen(
    [
        CHROME,
        f"--remote-debugging-port={PORT}",
        "--remote-allow-origins=*",
        "--headless=new",
        "--disable-gpu",
        "--disable-extensions",
        "--hide-scrollbars",
        f"--user-data-dir={UD}",
        "--window-size=1440,1100",
        "about:blank",
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

try:
    ws_url = None
    for _ in range(50):
        try:
            tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/list", timeout=1))
            pages = [t for t in tabs if t.get("type") == "page"]
            if pages:
                ws_url = pages[0]["webSocketDebuggerUrl"]
                break
        except Exception:
            time.sleep(0.2)
    if not ws_url:
        raise RuntimeError("no page target")

    ws = websocket.create_connection(ws_url, timeout=20)
    counter = [0]

    def cdp(method, params=None, timeout=30):
        counter[0] += 1
        msg_id = counter[0]
        ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
        deadline = time.time() + timeout
        while time.time() < deadline:
            data = json.loads(ws.recv())
            if data.get("id") == msg_id:
                if "error" in data:
                    raise RuntimeError(data["error"])
                return data.get("result") or {}
        raise TimeoutError(method)

    def js(expr, await_promise=False):
        res = cdp(
            "Runtime.evaluate",
            {"expression": expr, "returnByValue": True, "awaitPromise": await_promise},
        )
        if "exceptionDetails" in res:
            raise RuntimeError(res["exceptionDetails"])
        return (res.get("result") or {}).get("value")

    cdp("Page.enable")
    cdp("Runtime.enable")
    cdp(
        "Emulation.setEmulatedMedia",
        {"features": [{"name": "prefers-reduced-motion", "value": "reduce"}]},
    )
    cdp(
        "Emulation.setDeviceMetricsOverride",
        {"width": 1440, "height": 1100, "deviceScaleFactor": 1, "mobile": False},
    )

    jobs = [
        (
            "http://127.0.0.1:5173/#journey",
            'a.collage-item[href="experiences.html#exp-acydeai"]',
            OUT / "acydeai-collage-viewport.png",
        ),
        (
            "http://127.0.0.1:5173/experiences.html#exp-acydeai",
            "#exp-acydeai img[alt='ACYDEAI']",
            OUT / "acydeai-exp-viewport.png",
        ),
    ]

    for url, selector, dest in jobs:
        cdp("Page.navigate", {"url": url})
        time.sleep(2.4)
        js(
            f"""
            (async () => {{
              document.querySelectorAll('.gs-fade-up, .collage-item, .gs-exp-row, .gs-comp-wrapper').forEach((el) => {{
                el.style.opacity = '1';
                el.style.transform = 'none';
                el.style.visibility = 'visible';
              }});
              const el = document.querySelector({selector!r});
              if (!el) return false;
              el.scrollIntoView({{block:'center', behavior:'instant'}});
              await new Promise(r => setTimeout(r, 500));
              return true;
            }})()
            """,
            await_promise=True,
        )
        box = js(
            f"""
            (() => {{
              const el = document.querySelector({selector!r});
              if (!el) return null;
              const r = el.getBoundingClientRect();
              return {{
                x: r.x,
                y: r.y,
                width: r.width,
                height: r.height
              }};
            }})()
            """
        )
        print(selector, box, "href", js("location.href"))
        if not box:
            raise RuntimeError(selector)
        png = cdp("Page.captureScreenshot", {"format": "png", "fromSurface": True})
        dest.write_bytes(base64.b64decode(png["data"]))
        print("wrote viewport", dest, dest.stat().st_size)

    ws.close()
finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
