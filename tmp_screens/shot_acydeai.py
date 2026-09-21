import json, os, subprocess, time, base64, urllib.request
from pathlib import Path
import websocket

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PORT = 9348
UD = Path(os.environ["TEMP"]) / "acydeai-cdp7"
UD.mkdir(exist_ok=True)
OUT = Path(r"D:\personal web\Henok Demelash\tmp_screens")

proc = subprocess.Popen(
    [
        CHROME,
        f"--remote-debugging-port={PORT}",
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        f"--user-data-dir={UD}",
        "--window-size=1440,1100",
        "--remote-allow-origins=*",
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
time.sleep(1.4)

req = urllib.request.Request(
    f"http://127.0.0.1:{PORT}/json/new?http://localhost:5173/#journey",
    method="PUT",
)
tab = json.load(urllib.request.urlopen(req))
ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=20)
mid = 0


def cdp(method, params=None, timeout=25):
    global mid
    mid += 1
    msg_id = mid
    ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
    deadline = time.time() + timeout
    while time.time() < deadline:
        data = json.loads(ws.recv())
        if data.get("id") == msg_id:
            if "error" in data:
                raise RuntimeError(data["error"])
            return data.get("result", {})
    raise TimeoutError(method)


def eval_js(expr, await_promise=True):
    res = cdp(
        "Runtime.evaluate",
        {"expression": expr, "returnByValue": True, "awaitPromise": await_promise},
    )
    if "exceptionDetails" in res:
        raise RuntimeError(res["exceptionDetails"])
    return res.get("result", {}).get("value")


cdp("Page.enable")
cdp("Runtime.enable")
cdp(
    "Emulation.setEmulatedMedia",
    {"features": [{"name": "prefers-reduced-motion", "value": "reduce"}]},
)


def reveal_and_scroll(selector: str) -> None:
    eval_js(
        f"""
        (async () => {{
          if (window.gsap) {{
            window.gsap.set('.gs-fade-up, .collage-item, .gs-exp-row, .gs-comp-wrapper', {{
              opacity: 1, x: 0, y: 0, clearProps: 'transform'
            }});
          }}
          document.querySelectorAll('.gs-fade-up, .collage-item, .gs-exp-row').forEach((el) => {{
            el.style.opacity = '1';
            el.style.transform = 'none';
            el.style.visibility = 'visible';
          }});
          const el = document.querySelector({selector!r});
          if (!el) throw new Error('missing ' + {selector!r});
          el.scrollIntoView({{block: 'center', inline: 'nearest'}});
          await new Promise((r) => setTimeout(r, 800));
          return true;
        }})()
        """
    )


def shot_clip(url: str, selector: str, dest: Path) -> None:
    cdp("Page.navigate", {"url": url})
    found = None
    for _ in range(30):
        time.sleep(0.4)
        found = eval_js(
            f"""
            ({{
              href: location.href,
              title: document.title,
              ready: document.readyState,
              html: document.documentElement ? document.documentElement.outerHTML.length : 0,
              collage: Array.from(document.querySelectorAll('a.collage-item')).map(a => a.getAttribute('href')),
              hit: !!document.querySelector({selector!r}),
              box: (() => {{
                const el = document.querySelector({selector!r});
                if (!el) return null;
                const r = el.getBoundingClientRect();
                return {{x:r.x,y:r.y,width:r.width,height:r.height}};
              }})()
            }})
            """,
            await_promise=False,
        )
        box = (found or {}).get("box") or {}
        if found and found.get("hit") and found.get("ready") == "complete" and box.get("height", 0) > 80:
            break
    print("state", found)
    if not found or not found.get("hit"):
        raise RuntimeError(f"selector never appeared: {selector} state={found}")
    reveal_and_scroll(selector)
    box = eval_js(
        f"""
        (() => {{
          const el = document.querySelector({selector!r});
          if (!el) return null;
          const r = el.getBoundingClientRect();
          return {{x: r.x, y: r.y, width: r.width, height: r.height}};
        }})()
        """,
        await_promise=False,
    )
    print(selector, box)
    if not box or box["width"] < 40 or box["height"] < 40:
        raise RuntimeError(f"bad box for {selector}: {box}")
    # Viewport shot after scroll (reliable with reduced motion)
    vp = cdp("Page.captureScreenshot", {"format": "png", "fromSurface": True})
    (dest.parent / (dest.stem + "-viewport.png")).write_bytes(base64.b64decode(vp["data"]))
    clip = {
        "x": max(0, box["x"] - 12),
        "y": max(0, box["y"] - 12),
        "width": box["width"] + 24,
        "height": box["height"] + 24,
        "scale": 1,
    }
    res = cdp("Page.captureScreenshot", {"format": "png", "clip": clip, "fromSurface": True})
    dest.write_bytes(base64.b64decode(res["data"]))
    print("wrote", dest.name, dest.stat().st_size)


try:
    shot_clip(
        "http://localhost:5173/#journey",
        'a.collage-item[href="experiences.html#exp-acydeai"]',
        OUT / "acydeai-collage-tile.png",
    )
    shot_clip(
        "http://localhost:5173/experiences.html#exp-acydeai",
        "#exp-acydeai",
        OUT / "acydeai-exp-row.png",
    )
    shot_clip(
        "http://localhost:5173/experiences.html#exp-acydeai",
        "#exp-acydeai img[alt='ACYDEAI']",
        OUT / "acydeai-exp-tile.png",
    )
    print("done")
finally:
    ws.close()
    proc.terminate()
