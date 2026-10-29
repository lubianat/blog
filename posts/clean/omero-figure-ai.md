---
title: Drawing the OME logo in OME Figure with Claude
date: 2026-10-29
tags: omero, ome-zarr, ai, microscopy
---

# Drawing the OME logo in OME Figure with Claude



Josh Moore asked me to see if I could make the OME logo in OMERO.figure. Here it is:

<img src="../omero-figure-ai-files/images/ome_figure.png" alt="The OME logo made of nuclei in OMERO.figure" width="360">

[Open this figure in OME Figure](https://ome.github.io/figure?file=https://gist.githubusercontent.com/lubianat/93b763ef6844c3e9d7bb822583310e42/raw/80c8e232b3e5cc92b6271d56d4c5bf59dcceb899/figure.json)

It was a fun idea, specially because I wanted to test a thing: if Claude would do well in handling OME-figure.

And it worked! That worked because an OMERO.figure metadata is just a JSON file, and the images are public OME-Zarr files from the IDR.
The code is also open-source and relatively small, so the system could crawl and understand the full code base ([here is the full chat](https://claude.ai/share/8cfbe239-0e0b-406c-8ddd-f210c2514833)).


I drew both the OME and GerBI logo in [OMERO.figure](https://ome.github.io/figure/), with a microscopy image for every dot. You can [open the GerBI figure here](https://ome.github.io/figure?file=https://gist.githubusercontent.com/lubianat/93b763ef6844c3e9d7bb822583310e42/raw/80c8e232b3e5cc92b6271d56d4c5bf59dcceb899/figure.json), right in your browser.


The point of this post: tools like OME Figure, open and with plain text configs, are already ready for AI. With OME-Zarr data on top, everyday AI apps can already help people make FAIR (and fun) figures from real microscopy data.

## What I made

I started from a screenshot of each logo, the OMERO.figure source code, and public images from the IDR.

First the OME logo: six panels of the same IDR image (idr0062A), placed in a ring and coloured like the dots.

![The OME logo](../omero-figure-ai-files/images/ome_logo.png)

Then I got the system to turn off the borders and used a white background with inverted lookup tables. Inverting also flips the colour, so the AI set each channel to the opposite colour to get the right one back.

<img src="../omero-figure-ai-files/images/ome_figure_first_try.png" alt="First try: inverting flipped the colours" width="360">

<img src="../omero-figure-ai-files/images/ome_figure.png" alt="The OME logo made of nuclei in OMERO.figure" width="360">

[Open this figure in OME Figure](https://ome.github.io/figure?file=https://gist.githubusercontent.com/lubianat/93b763ef6844c3e9d7bb822583310e42/raw/80c8e232b3e5cc92b6271d56d4c5bf59dcceb899/figure.json)

Then GerBI. 92 panels is too many to write by hand, so I asked for a [Python script that writes the JSON](https://github.com/lubianat/logo-gerbi-ome-figure). It took the dot positions from a screenshot of the logo, and lined up the grey dots on their grid.

![The GerBI logo](../omero-figure-ai-files/images/gerbi_logo.png)

[Open this version in OMERO.figure](https://ome.github.io/figure/?file=https://gist.githubusercontent.com/lubianat/cf16d8bc13f2e4e6bb0aec342f1dfbf3/raw/17f97a04c3548f315cdb807b2fc47c101bbb4817/gerbi_logo_figure.json)

Next, every dot got a different Z plane. Then I zoomed in on a few panels by hand and asked the script to use that style everywhere.

![Halfway: every dot a different Z plane](../omero-figure-ai-files/images/gerbi_halfway.png)

[Open this version in OMERO.figure](https://ome.github.io/figure/?file=https://gist.githubusercontent.com/lubianat/214df9866b3a9835e70ca10bd1e8afd2/raw/de0bdc08e3588d7d93e8271d5e139eeaab1e6b2a/nuclei_as_gerbi_logo_figure.json)

Last step: a Cell Painting image from idr0033A. The script read the OME-Zarr, found the nuclei and kept the 15 that stand out the most. These are used to draw the logo.

![The Cell Painting image, DNA channel](../omero-figure-ai-files/images/cellpainting.png)

![GerBI logo from the 15 most isolated nuclei (test run on a screenshot of the image)](../omero-figure-ai-files/images/gerbi_nuclei_test_render.png)

[Open the latest version in OMERO.figure](https://ome.github.io/figure?file=https://gist.githubusercontent.com/lubianat/93b763ef6844c3e9d7bb822583310e42/raw/80c8e232b3e5cc92b6271d56d4c5bf59dcceb899/figure.json)

Each time, I loaded the JSON in OMERO.figure, had a look, and said what to change.

## Where OME-Zarr comes in

OME Figure started as OMERO Figure, which meant you needed to deploy an OMERO server to use it. And to deploy it _publically_ for sharing the figures.

The OME-Zarr made everything much more portable. Each image is a URL, and its metadata sits next to the pixels as JSON.

There are still _a lot_ of benefits of using OMERO, and OMERO+OME-Zarr integration is getting better and better. But modularity is a good thing, and this little experiment is a reminder that you can already do a lot with just OME-Zarr.

## Claude is not magic

Claude is not magic, so tweaks and checks are needed for making it work with figure.

For example, it got the inverted colours wrong. One look at the result in OMERO.figure showed the problem, and the fix was quick.

In our first GerBI screenshot, Claude messed up a bit the format of the microscope. But fixing it was surprisingly easy.

None of this was a big deal, since the output was a text file I could load and check in seconds.

So, not magic, but a very useful tool for OME figure users. Maybe we can improve integration at some poitn in the future, but it already works pretty well.


## Try it yourself

You don't need an OMERO server for any of this. OMERO.figure runs in the browser at [ome.github.io/figure](https://ome.github.io/figure/), and it can open a figure JSON straight from a URL.

There is a big set of open images to explore at https://ngff.openmicroscopy.org/data/, and some curated datasets at https://idr.github.io/ome-ngff-samples/.

And here is [the full chat with the AI](https://claude.ai/share/8cfbe239-0e0b-406c-8ddd-f210c2514833), if you want to see how it went, mistakes included.

Have fun! I surely did.
