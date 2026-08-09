#!/usr/bin/env python3
"""Rebuild the apps table in README.md between the APPS markers.

Source of truth: https://cjcombs.com/apps.json (override with APPS_JSON_URL).
If the URL is unreachable or doesn't return valid JSON, falls back to the
apps.json in this repo — the profile never breaks when the site is down.

Adding an app = adding one object to apps.json:
  { "name": "...", "platform": "iOS", "status": "Built",
    "description": "One line.", "url": "https://... (optional)" }
"""
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README = os.path.join(ROOT, "README.md")
LOCAL = os.path.join(ROOT, "apps.json")
URL = os.environ.get("APPS_JSON_URL", "https://cjcombs.com/apps.json")
START, END = "<!-- APPS:START -->", "<!-- APPS:END -->"


def load_apps():
    """Return (apps, source) — live URL first, local apps.json as fallback."""
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "cjcombs-profile-sync"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
        apps = data.get("apps") if isinstance(data, dict) else data
        if isinstance(apps, list) and apps and all(isinstance(a, dict) and a.get("name") for a in apps):
            return apps, URL
        raise ValueError("unexpected JSON shape")
    except Exception as exc:
        print(f"note: {URL} unusable ({exc}); using local apps.json")
        with open(LOCAL, encoding="utf-8") as f:
            data = json.load(f)
        return (data.get("apps") if isinstance(data, dict) else data), "apps.json"


def render(apps):
    """Emit an HTML table mirroring the site's app rows: screenshot left,
    name + platform/status chips + description + tag chips right."""
    if not apps:
        return "_No apps listed yet._"
    rows = []
    for app in apps:
        name = app["name"].strip()
        url = app.get("url", "https://cjcombs.com/#apps")
        title = f'<a href="{app["url"]}"><b>{name}</b></a>' if app.get("url") else f"<b>{name}</b>"
        chips = " ".join(
            f"<code>{c}</code>" for c in (app.get("platform"), app.get("status")) if c
        )
        tags = " ".join(f"<code>{t}</code>" for t in app.get("tags", []))
        tags_html = f"<br><sub>{tags}</sub>" if tags else ""
        shot = (
            f'<a href="{url}"><img src="{app["image"]}" alt="{name}" width="180"></a>'
            if app.get("image")
            else ""
        )
        rows.append(
            "  <tr>\n"
            f'    <td width="200" valign="top">{shot}</td>\n'
            f'    <td valign="top">{title} {chips}<br>{app.get("description", "")}{tags_html}</td>\n'
            "  </tr>"
        )
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def main():
    apps, source = load_apps()
    with open(README, encoding="utf-8") as f:
        old = f.read()
    if START not in old or END not in old:
        sys.exit(f"error: markers {START} / {END} missing from README.md")
    new = re.sub(
        re.escape(START) + r".*?" + re.escape(END),
        f"{START}\n{render(apps)}\n{END}",
        old,
        flags=re.S,
    )
    if new != old:
        with open(README, "w", encoding="utf-8") as f:
            f.write(new)
        print(f"updated README.md — {len(apps)} apps from {source}")
    else:
        print(f"README.md already current ({len(apps)} apps from {source})")


if __name__ == "__main__":
    main()
