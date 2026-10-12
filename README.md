# Terrill Li — mathematics website

This is a Quarto website intended for GitHub Pages. Its editable source lives here, separately from the Obsidian vault at `~/Desktop/Mathematics`.

The three selected source folders are declared in `publish-map.yml`. The sync script reads them without modifying the vault. Existing website pages retain their English editorial changes; new or changed source notes are staged in `.sync-pending/` for review rather than placed directly on the site.

To inspect source changes locally:

```sh
python3 scripts/sync_notes.py --vault "$HOME/Desktop/Mathematics"
```

To refresh the pending copies and navigation indexes:

```sh
python3 scripts/sync_notes.py --vault "$HOME/Desktop/Mathematics" --sync
```

Translate and review a staged QMD before copying it into `notes/`. After accepting a source revision, record its hash with `--acknowledge 'folder/name.md'` using its vault-relative path. The website copy may intentionally differ from the original. Build and preview with:

```sh
/Applications/RStudio.app/Contents/Resources/app/quarto/bin/quarto render
python3 -m http.server 8765 --bind 127.0.0.1 --directory _site
```

The GitHub Actions workflow deploys whenever `main` is pushed. Publication therefore requires explicit approval before any push.
