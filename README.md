<p align="center">
  <img src="docs/khaneh-banner.svg" alt="Khaneh · خانه · A home for memory, framed by Persian-inspired floral ornament in lapis blue and gold" width="900">
</p>

<p align="center"><em>Khaneh (خانه) means home in Persian.</em></p>

## Why I built Khaneh

I built Khaneh to preserve the stories of people who lost their lives during protests in Iran. I wanted to create a place where someone could spend time with a portrait, read about a person's life, and discover the interests and dreams behind their name.

This project matters to me because I want these lives to be remembered. I brought Persian art, garden motifs, and the colours of illuminated manuscripts into the design to give their stories a home. It is a way for me to use what I am learning in software to build something meaningful.

<p align="center"><img src="docs/khaneh-divider.svg" alt="" width="360"></p>

## Inside Khaneh

- **An atlas of lives.** Explore portraits and biographies, with sources alongside each story.
- **A space for remembrance.** Interactive sculpture studies honour Hamid and Khodanoor through artistic interpretations of their stories.
- **Ask the archive.** Search by meaning and ask questions about the collected stories, with answers drawn from reviewed passages and linked to their sources.

## What I used

- **JavaScript, HTML and CSS** for the Persian-inspired interface, interactive map, and portrait stories.
- **Go** for the REST API that serves memorial records and connects the frontend to the AI service.
- **Python, FastAPI and PyTorch** for semantic search and source-linked answers, using pretrained models that run locally on CPU.
- **Blender and WebGL** to create the sculpture models and display them as interactive particle figures in the browser.

<details>
<summary><strong>Run it locally</strong></summary>

With Go 1.22+ and Node.js installed, open two terminals at the repository root.

Start the API:

```sh
cd outputs/khaneh-api
go run .
```

Start the frontend in the other terminal:

```sh
node scripts/preview.cjs
```

Open [Khaneh](http://127.0.0.1:4173/). To enable **Ask the archive**, follow the [local AI setup](outputs/khaneh-search/README.md). The AI runs on CPU and searches the collected archive; it does not browse the web.

[API details](outputs/khaneh-api/README.md) · [Tests and benchmarks](benchmarks/README.md)

</details>

