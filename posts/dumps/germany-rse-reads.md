# Technical reading list for a bioimaging + semantic web trip through Germany and Amsterdam

*Tiago & AI — summary of an AI conversation that may be useful to others.*

This is a reading list for a very specific kind of trip: attending a bioimaging community meeting (GerBI in Fulda), visiting friends in Jena and Bonn, and ending at SWAT4HCLS 2026 in Amsterdam. The person traveling works as a Research Software Engineer supporting the Zarr standard and bioimage metadata, does JSON-LD/RDF work, is very active on Wikidata and iNaturalist, and has a PhD on managing cell types in Wikidata. The recommendations lean technical and encyclopedic, meant for eReaders on planes and trains. Some are in German (B1/B2 level).

The list is split into two halves: general interest reading for airports and downtime, and deep technical reading that directly feeds into the work discussed at the conferences.

---

## General interest

### Plant systematics & botany

- *The Plant Hunters* by Carolyn Fry — history of botanical exploration, encyclopedic but readable.
- *The Cabaret of Plants* by Richard Mabey — cultural and scientific history of plants, touching on systematics and evolution.
- *Plant Systematics: A Phylogenetic Approach* by Judd et al. — the heavy reference classic. Good for dipping into on long flights.
- *Die Botanik der Lust* by Michael Pollan (German translation of *The Botany of Desire*) — four plants and how they shaped civilization. Accessible B1/B2 German.

### Biodiversity & natural history

- *The Song of the Dodo* by David Quammen — island biogeography, extinction, and biodiversity. Long but compulsively readable.
- *Das sechste Sterben* by Elizabeth Kolbert (German translation of *The Sixth Extinction*) — biodiversity loss told through field reporting. Well-written, accessible German.
- *An Immense World* by Ed Yong — animal sensory biology (Umwelten). Light, encyclopedic, recent.
- *Die Naturgeschichte* by Pliny the Elder — the original encyclopedia of the natural world. Good abridged translations exist in both English and German.

### Germany — history, culture & places

- *Jena 1800: Die Republik der freien Geister* by Peter Neumann — the remarkable intellectual circle in Jena around 1800 (Goethe, Schiller, Hegel, the Romantics). Perfect to read on the train to Jena. Accessible German.
- *Die Vermessung der Welt* by Daniel Kehlmann — a novel about Alexander von Humboldt and Carl Friedrich Gauss. Funny, clever, good B1/B2 German. Connects biodiversity and German intellectual history.
- *German Genius* by Peter Watson — encyclopedic (1000+ pages) history of German contributions to science, philosophy, and culture. Good for dipping in and out.

### Cross-disciplinary classics

- *Gödel, Escher, Bach* by Douglas Hofstadter — logic, systems, patterns, creativity. Long but perfect for trains.
- *The Information: A History, a Theory, a Flood* by James Gleick — information theory from African drums to Wikipedia.
- Borges, *Collected Fictions* — short stories about infinite libraries, encyclopedias, and taxonomies. "The Library of Babel" and "Tlön, Uqbar, Orbis Tertius" are basically about classification systems and collaborative knowledge.

---

## Deep technical reading

### Zarr, OME-NGFF & bioimaging data

The **Zarr v3 core specification** (zarr-specs.readthedocs.io) deserves a careful end-to-end read. Not long, but the codec pipeline, sharding, and extension mechanism sections reward close attention. Print-to-PDF for eReader.

The **OME-NGFF spec** at ngff.openmicroscopy.org/latest defines how multiscale, multidimensional bioimaging arrays should be structured in Zarr — axes metadata, coordinate transformations, labeling. Read alongside the foundational 2021 Nature Methods paper:

- Moore et al., "OME-NGFF: a next-generation file format for expanding bioimaging data-access strategies" (Nature Methods, 2021).

The broader community companion piece:

- Moore, Basurto-Lozada, Besson et al., "OME-Zarr: a cloud-optimized bioimaging file format with international community support" (2023).

The 2024 OME-NGFF Hackathon preprint (Lüthi et al., 2025, BioHackrXiv) documents outcomes from the Zürich hackathon — workflow results and current tooling around OME-Zarr. Very fresh.

The **OME-Zarr 1.0 RFC process** is actively happening. The open RFCs on the ome/ngff GitHub repo (especially RFC5 on transforms) are worth reading closely. Download the markdown ahead of time.

The **Zarr v3 extension registry** on GitHub (zarr-developers/zarr-extensions) maps the current extension landscape. Worth reviewing for anyone working at the OME-NGFF/Zarr intersection.

### Semantic web, JSON-LD, RDF & knowledge graphs

- *Semantic Web for the Working Ontologist* by Allemang & Hendler (3rd edition) — covers RDF 1.1, SPARQL 1.1, OWL 2, and JSON-LD. The single best book for SWAT4HCLS prep.
- *Learning SPARQL* by Bob DuCharme (O'Reilly) — more practical and query-focused. Pairs well with the Wikibooks SPARQL tutorial for Wikidata-specific patterns.
- The **W3C JSON-LD 1.1 spec** — reads surprisingly well as a document. Understanding framing, compaction, and context resolution deeply helps with metadata work. Free at w3.org.
- *Knowledge Graphs* by Aidan Hogan et al. (2021, MIT Press / free preprint from authors) — the rigorous encyclopedic textbook. Covers RDF, SPARQL, OWL, SHACL, knowledge graph embeddings.
- *Linked Data Patterns* by Leigh Dodds & Ian Davis — free online, short, practical. A pattern language for linked data design decisions.
- The **SHACL specification** and SHACL Advanced Features spec — increasingly important for anyone doing validation of metadata in RDF.

### Wikidata, biodiversity informatics & ontologies

- Waagmeester, Stupp, Burgstaller-Muehlbacher et al., "Wikidata as a FAIR knowledge graph for the life sciences" (2020) — the canonical paper on biomedical Wikidata.
- The 2024 framework paper on integrating biomedical knowledge in Wikidata with OBO ontologies and MeSH keywords (Heliyon) — evaluates semantic alignment gaps and proposes automated enrichment methods.
- Smith et al., "The OBO Foundry: coordinated evolution of ontologies" (Nature Biotechnology, 2007) and the updated 2024 community paper — foundational for understanding how biomedical ontologies are governed.
- *Ontology Engineering* by Keet (Springer, free chapters online) — the best modern textbook on building and maintaining ontologies.
- The TDWG **Darwin Core specification** and recent papers on Wikidata for biodiversity (connecting iNaturalist, GBIF, and Wikidata).

### RSE practice, FAIR software & infrastructure

- **The Turing Way** (book.the-turing-way.org) — community-maintained handbook for reproducible, ethical, and collaborative data science. The FAIR data and FAIR software chapters especially. Free, works well as PDF on eReader.
- The **Research Software Engineering** book by Matt Bannister (Chapman & Hall/CRC, free online at rse-book.github.io) — big picture overview of software carpentry-level skills, automation, and reproducibility for researchers.
- Barker et al., "Introducing the FAIR Principles for Research Software" (Scientific Data, 2022) — the FAIR4RS Principles paper. Short but foundational.
- The NFDI working group on RSE has published a layered model of RSE roles and responsibilities in research data infrastructure, connecting FAIR4RS principles with practical tooling — relevant for anyone working in the German research infrastructure ecosystem (NFDI4BIOIMAGE, GerBI).
- *Software Engineering at Google* (Winters, Manshreck, Wright) — free online. Not research-specific, but the chapters on code review, testing culture, and dependency management are useful for any RSE thinking about long-term maintainability.

---

## Conference-specific prep

For **GerBI in Fulda** (March 16–18): the OME-NGFF specs, RFCs, and NFDI4BIOIMAGE publications are the most directly relevant reading. The hackathon preprint and the Zarr v3 extension registry map the current state of the community.

For **SWAT4HCLS in Amsterdam** (March 23–26): the Allemang book, the JSON-LD spec, and the Wikidata-as-FAIR-KG paper are the core prep. The BioHackathon project pitches are already posted on the SWAT4HCLS website — reviewing them on the train is good preparation for joining a hackathon project. The conference accepts short papers, position papers, demos, and posters on topics including bioimaging, biodiversity, knowledge graphs, and FAIR data.

The itinerary works well for reading progression: specs and bioimaging reading on the outbound flights, semantic web and SPARQL on the trains through Jena and Bonn, arrive in Amsterdam with context for the hackathon.
