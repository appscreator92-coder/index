import json
import re
import urllib.parse
import urllib.request

PLAYLIST_URL = "https://premiumplugx.me/vzy/playlist.php"
OUTPUT_FILE = "zee5.json"
IDX1_BASE = "https://hdlivetv.gt.tc/livetv/tv/zee5/zee5.php?id="


def fetch_playlist(url: str, retries: int = 3) -> str:
    headers = {"User-Agent": "Mozilla/5.0"}
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as exc:
            last_error = exc
            if attempt == retries:
                raise RuntimeError(f"Failed to fetch {url} after {retries} attempts: {exc}") from exc
    raise RuntimeError(f"Unexpected error: {last_error}")


def extract_attr(line: str, attr: str) -> str:
    match = re.search(rf'{re.escape(attr)}="([^"]*)"', line)
    return match.group(1) if match else ""


def parse_m3u(content: str) -> list[dict]:
    entries = []
    current = None

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line == "#EXTM3U":
            continue

        if line.startswith("#EXTINF:"):
            tvg_id = extract_attr(line, "tvg-id")
            tvg_name = extract_attr(line, "tvg-name")
            tvg_logo = extract_attr(line, "tvg-logo")

            if not tvg_name and "," in line:
                tvg_name = line.split(",", 1)[1].strip()

            # Matches your sample format like "%26PicturesHD"
            encoded_id = urllib.parse.quote(tvg_name.replace(" ", ""), safe="")

            current = {
                "keyId": "",
                "key": "",
                "name": tvg_name,
                "id": tvg_id,
                "idx1": f"{IDX1_BASE}{encoded_id}",
                "logo": tvg_logo,
                "url": "",
            }

        elif line.startswith("#KODIPROP:inputstream.adaptive.license_key=") and current is not None:
            raw_key = line.split("=", 1)[1].strip()
            if ":" in raw_key:
                key_id, key_val = raw_key.split(":", 1)
                current["keyId"] = key_id.strip()
                current["key"] = key_val.strip()

        elif not line.startswith("#") and current is not None:
            current["url"] = line
            entries.append(current)
            current = None

    return entries


def main() -> None:
    content = fetch_playlist(PLAYLIST_URL)
    data = parse_m3u(content)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"Wrote {len(data)} channels to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
