# Cheshire KB Starter

- All school URLs are in `urls.txt`.
- GitHub Actions (`.github/workflows/refresh.yml`) will crawl & extract text → `dist/*.txt`,
  then push them into your Hugging Face Space's `sources/`.
- Set repo secrets:
  - `HF_TOKEN`  (Hugging Face Access Token with **write** scope)
  - `HF_SPACE`  (like `spaces/<username>/<space_name>`)

Run it from the **Actions** tab → **Refresh KB** → **Run workflow**.
