---
title: OMERO.figure is already AI-ready
date: 2026-10-29
tags: omero, ome-zarr, ai, microscopy
---

# OMERO.figure is already AI-ready

We drew the GerBI logo in [OMERO.figure](https://ome.github.io/figure/), with a microscopy image for every dot. You can [open the figure here](https://ome.github.io/figure?file=https://gist.githubusercontent.com/lubianat/93b763ef6844c3e9d7bb822583310e42/raw/80c8e232b3e5cc92b6271d56d4c5bf59dcceb899/figure.json), right in your browser.

We didn't place the panels by hand. An AI chat app wrote the figure for us ([here is the full chat](https://claude.ai/share/8cfbe239-0e0b-406c-8ddd-f210c2514833)). That worked because an OMERO.figure figure is just a JSON file, and the images are public OME-Zarr files from the IDR.

The point of this post: tools that save everything as plain text are already ready for AI. With OME-Zarr data on top, everyday AI apps could soon help people make FAIR figures from real data.

## What we made

We started from a screenshot of each logo, the OMERO.figure source code, and public images from the IDR.

First the OME logo: six panels of the same IDR image (idr0062A), placed in a ring and coloured like the dots.

![The OME logo](../omero-figure-ai-files/images/ome_logo.png)

Then we turned off the borders and used a white background with inverted lookup tables. Inverting also flips the colour, so the AI set each channel to the opposite colour to get the right one back.

![First try: inverting flipped the colours](../omero-figure-ai-files/images/ome_figure_first_try.png)

![The OME logo made of nuclei in OMERO.figure](../omero-figure-ai-files/images/ome_figure.png)

Then GerBI. 92 panels is too many to write by hand, so we asked for a Python script that writes the JSON. It took the dot positions from a screenshot of the logo, and lined up the grey dots on their grid.

![The GerBI logo](../omero-figure-ai-files/images/gerbi_logo.png)

[Open this version in OMERO.figure](https://ome.github.io/figure/?file=https://gist.githubusercontent.com/lubianat/cf16d8bc13f2e4e6bb0aec342f1dfbf3/raw/17f97a04c3548f315cdb807b2fc47c101bbb4817/gerbi_logo_figure.json)

Next, every dot got a different Z plane. Then we zoomed a few panels by hand onto single nuclei, and asked the script to use that style everywhere.

![Halfway: every dot a different Z plane](../omero-figure-ai-files/images/gerbi_halfway.png)

[Open this version in OMERO.figure](https://ome.github.io/figure/?file=https://gist.githubusercontent.com/lubianat/214df9866b3a9835e70ca10bd1e8afd2/raw/de0bdc08e3588d7d93e8271d5e139eeaab1e6b2a/nuclei_as_gerbi_logo_figure.json)

Last step: a Cell Painting image from idr0033A. The script reads the OME-Zarr, finds the DNA channel, finds the nuclei and keeps the 15 that are most on their own. Those become the crops that draw the logo.

![The Cell Painting image, DNA channel](../omero-figure-ai-files/images/cellpainting.png)

![GerBI logo from the 15 most isolated nuclei (test run on a screenshot of the image)](../omero-figure-ai-files/images/gerbi_nuclei_test_render.png)

[Open the latest version in OMERO.figure](https://ome.github.io/figure?file=https://gist.githubusercontent.com/lubianat/93b763ef6844c3e9d7bb822583310e42/raw/80c8e232b3e5cc92b6271d56d4c5bf59dcceb899/figure.json)

Each time, we loaded the JSON in OMERO.figure, had a look, and said what to change.

## Why it worked

OMERO.figure saves the whole figure as one JSON file. You can export it and import it from the File menu.

Everything is in there: where each panel sits and how big it is, which image, which Z plane, the channels and their colours, contrast, zoom, rotation, borders, labels. The AI learned the format by reading the OMERO.figure code. It never had to touch OMERO.figure itself. It wrote text, and we pasted it in.

Once the layout was in a script, changes got easy. Panel size, colours, number of nuclei: each is just a number at the top of the file.

So OMERO.figure didn't need any AI features to work with AI. It just needed to keep everything in a format that is open and easy to read.

## Where OME-Zarr comes in

OME-Zarr made the images just as easy to work with as the figure. Each image is a URL, and its metadata sits next to the pixels as JSON.

In the figure, each panel just points to that URL. No login, no server IDs, no export. The script read the axes, pixel sizes and channel names from the metadata, and used them to find the DNA channel and size the crops. Standard Python tools could read the pixels straight from the IDR, so the AI could write code that picks the cells, not just code that places them.

And anyone who opens the final JSON can see exactly which image, plane, crop and contrast each panel uses.

## What went wrong

The AI made mistakes, and we had to check every step.

At first it couldn't reach the IDR server, so it filled in the image sizes from memory. We fixed that by having the script read the real metadata when we run it.

It also got the inverted colours wrong. One look at the result in OMERO.figure showed the problem, and the fix was quick.

In our first GerBI screenshot, a tooltip hid half the logo. The AI guessed the missing dots, and they looked wrong until we sent a clean image.

And the taste was ours. We picked the first close-ups by hand, and the script copied that style.

None of this was a big deal, since the output was a text file we could load and check in seconds.

## What's next: FAIR figures from a chat app

If you can draw a logo this way, you can make a real figure. Soon, everyday AI apps could help people make figures straight from public OME-Zarr data, and keep them FAIR.

The panels point to public URLs, so you can share the figure as a JSON file and anyone can open it. OME-Zarr and the figure JSON are open formats that any tool can read and write. The JSON keeps every choice, and the script keeps the rule for picking the cells, like "the 15 most isolated nuclei on the middle plane".

Picture asking: "Show me the five most isolated nuclei from each condition in this IDR study, same contrast, with scale bars." The AI reads the metadata, picks the cells, and gives you a figure you can open, tweak and publish with its recipe.

We don't need new tools for this. We need tools that save their state in open formats, and data that lives at stable URLs. OMERO.figure and OME-Zarr already do both.

## Try it yourself

You don't need an OMERO server for any of this. OMERO.figure runs in the browser at [ome.github.io/figure](https://ome.github.io/figure/), and it can open a figure JSON straight from a URL. As a colleague put it: "No OMERO → go figure".

The images load from the IDR, so the first view can take a little while.

And here is [the full chat with the AI](https://claude.ai/share/8cfbe239-0e0b-406c-8ddd-f210c2514833), if you want to see how it went, mistakes included.
