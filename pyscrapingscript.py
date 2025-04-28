import os
import requests
from bs4 import BeautifulSoup

# ─ CONFIGURATION ──────────────────────────────────────────────────────────────
BASE_URL        = 'https://www.ncei.noaa.gov/data/global-summary-of-the-year/access/'
DOWNLOAD_DIR    = 'gsod_csv'
CHECKPOINT_FILE = 'checkpoint.txt'
CHUNK_SIZE      = 41014
# ────────────────────────────────────────────────────────────────────────────────

def get_csv_urls():
    resp = requests.get(BASE_URL)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    urls = [BASE_URL + a['href']
            for a in soup.find_all('a', href=True)
            if a['href'].lower().endswith('.csv')]
    return sorted(urls)

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE) as f:
            text = f.read().strip()
            return int(text) if text.isdigit() else 0
    return 0

def save_checkpoint(idx):
    with open(CHECKPOINT_FILE, 'w') as f:
        f.write(str(idx))

def download_file(url):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    fname = os.path.join(DOWNLOAD_DIR, os.path.basename(url))
    if os.path.exists(fname):
        return
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(fname, 'wb') as w:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    w.write(chunk)

def main():
    urls      = get_csv_urls()
    total     = len(urls)
    start_idx = load_checkpoint()
    end_idx   = min(total, start_idx + CHUNK_SIZE)

    if start_idx >= total:
        print("✅ All files already downloaded.")
        return

    last_idx = start_idx
    for i in range(start_idx, end_idx):
        url = urls[i]
        print(f"[{i+1}/{total}] Downloading {url}")
        try:
            download_file(url)
            last_idx = i + 1   # record the last successful 1-based index
            save_checkpoint(last_idx)
        except Exception as e:
            print(f"❌ Error on {url}: {e}")
            break

    print()
    print(f"⏱ Finished downloading files {start_idx+1}–{last_idx}")
    if last_idx < total:
        print(f"➡️ Next run will resume at index {last_idx+1}")
    else:
        print("🎉 All done!")

if __name__ == '__main__':
    main()
