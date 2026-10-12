# Terrill Li — Mathematics Website

I am an undergraduate mathematics student at the University of Sydney. This repository contains the source for my [personal website](https://terrillli-math.github.io/).

The site is a record of what I am learning. It includes [course notes](https://terrillli-math.github.io/notes/math1964/), [short explorations](https://terrillli-math.github.io/notes/atomization/), and [background topics](https://terrillli-math.github.io/notes/appendix/). These are working notes. I revise them as my understanding grows, and I mark proofs that are still in progress.

## How the site is made

The pages are written in [Quarto](https://quarto.org/) and published with GitHub Pages. The `.qmd` files in `notes/` are edited versions for the website. They may differ from my private study notes in wording, layout, or mathematical corrections.

To build the site locally, install Quarto and run:

```sh
quarto render
```

Quarto creates the website in `_site/`. The source pages, not the generated output, are kept in this repository.
