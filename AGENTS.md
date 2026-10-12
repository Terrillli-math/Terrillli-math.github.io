# Mathematics website workflow

- Treat the Obsidian vault at `~/Desktop/Mathematics` as read-only. Never edit, rename, or delete files in that vault.
- Only inspect `.md` and `.qmd` files inside the three source folders in `publish-map.yml`. Do not silently broaden the selection.
- The website project in this directory is the editable copy. All public-facing prose, titles, navigation, and notes must be readable English. Use short sentences and familiar words, between academic writing and natural explanation. Keep necessary mathematical terms and explain them. Preserve mathematical meaning; distinguish a translation from a substantive correction.
- `python3 scripts/sync_notes.py --vault "$HOME/Desktop/Mathematics" --sync` stages newly found notes or changes under `.sync-pending/`. Review and translate the staged copy before adding a website page. Never publish the raw generated text automatically.
- Keep a short record of substantive mathematical corrections in `EDITORIAL_REVIEW.md` so the user can check them. Do not treat the website's corrections as authority to change the original notes.
- Render with `/Applications/RStudio.app/Contents/Resources/app/quarto/bin/quarto render` and inspect the local result.
- Do not push to GitHub or trigger the publishing workflow without the user's explicit approval. A push to `main` deploys the site.
