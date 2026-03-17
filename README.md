# MASEO: A Multi-Agent System for Explainable Ontology Generation
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19052004.svg)](https://doi.org/10.5281/zenodo.19052004)

This repository provides the artifact for `MASEO`, a research-oriented multi-agent system that automated generate ontologies from competency questions, with a built-in focus on explainability. It aims to make the process of ontology generation more transparent, modular, and intelligent by distributing tasks among specialized agents. Each specialized agent is designed to keep track the logic behind each entity in generated ontology. 

## Project Structure

```bash

masoe/
├── dataset/          # Contains competency questions, generated & gold standard ontologies, run-time log
├── src/              # The core source code for the multi-agent system.
│   └── ...           # (Includes agent implementations, evaluation code)
└── README.md         # This file.

```

## MASOE Structural Overview

The pipeline consists of four sequential stages:

| Agent | Model | Responsibility |
|-------|-------|----------------|
| `Ontology Generation Agent` | `deepseek-reasoner` | Generates the initial OWL ontology from CQs |
| `Syntax Repair Agent` | `deepseek-reasoner` | Fixes RDF/XML syntax errors reported by the parser |
| `Logical Consistency Agent` | `deepseek-reasoner` | Repairs logical inconsistencies reported by HermiT |
| `Pitfall Resolution Agent` | `deepseek-reasoner` | Resolves ontology modeling pitfalls reported by OOPS! |

The illustration of the MASOE framework:

![Multi-Agent Ontology Generation Pipeline](src/image/maseo_framework.png)

---

## Features

- **End-to-end automation** — from a list of CQs to a validated ontology
- **Role-based agents** — each stage is handled by a dedicated LLM agent with a specific instruction and responsibility
- **Provenance tracking** — every ontology entity carries an append-only `vaem:rationale` log attributed to the agent that made each change, and a `dc:source` log linking each change back to the CQ, pitfall, or error that motivated it

---

## Requirements

### Python dependencies

```bash
pip install agno rdflib requests beautifulsoup4 pydantic
```

### External tools

| Tool | Purpose | Setup |
|------|---------|-------|
| [HermiT Reasoner](http://www.hermit-reasoner.com/) | Logical consistency checking | Download `HermiT.jar` and update the path in `reason_ontology()` |
| [OOPS! REST API](https://oops.linkeddata.es/) | Ontology pitfall detection | No local setup required — uses the public REST endpoint |
| Java (JRE 8+) | Required to run HermiT | `sudo apt install default-jre` |

---

## Configuration

Before running, update the following constants at the top of `agent_framework.py`:

```bash
# Instaill java and ollama in you system
sudo apt update
sudo apt install deflault-jre
sudo apt install curl
curl -fsSL https://ollama.com/install.sh | sh
ollama pull embeddinggemma
ollama serve
```
Make the changes in the `agent_framework.py` to ensure the correctness of variables. 
```python

# Path to your OOPS! request template
REQUEST_TEMPLATE = "/path/to/oops_request_template.xml"

# Path to HermiT JAR inside reason_ontology()
"java", "-jar", "/path/to/HermiT.jar"
```
---

## Usage

```bash
python agent_framework.py \
    --api_key      YOUR_DEEPSEEK_API_KEY \
    --cqs_file     path/to/competency_questions.json \
    --save_file    path/to/output_ontology.owl \
    --agent_method true
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--api_key` | Yes | DeepSeek API key |
| `--cqs_file` | Yes | Path to a JSON file containing the list of competency questions |
| `--save_file` | Yes | Path where the final OWL ontology will be saved |
| `--agent_method` | No | `true` runs the full 4-stage pipeline; `false` runs generation only (default: `false`) |

### CQs file format

The CQs file should be a JSON array of strings:

```json
[
  "What is the genre of a game?",
  "Which players have purchased an in-app item?",
  "What is the username of a player?",
...
]
```

---

## Ontology Entity Structure

Each generated ontology entity is a structured object with the following fields:

| Field | Definition | Example value |
|-------|-----------|---------------|
| **Type** (`rdf:type`) | Indicates whether the entity is an `owl:Class`, `owl:ObjectProperty`, or `owl:DatatypeProperty`. | `:Player rdf:type owl:Class;` `:hasUsername rdf:type owl:DatatypeProperty` |
| **Label** (`rdfs:label`) | Provides a human-readable name for the entity. | `"Player"` ; `"has username"` |
| **Comment** (`rdfs:comment`) | Provides a textual description of the meaning of the entity. | `"A person who plays games."` ; `"Relates a player to the player's username."` |
| **Rationale** (`vaem:rationale`) | Records the justification for entity creation or modification across refinement iterations. | `"Derived from CQ [number] about the username of a player."` |
| **Source** (`dc:Source`) | Records the CQ or validation feedback from which the entity or revision was derived. | `"What is the username of the player?"` |
| **Subclass of** (`rdfs:subClassOf`) | (Classes only) Records subclass relations or logical restrictions involving the class. | `:Player rdfs:SubClassOf :Human` |
| **Domain** (`rdfs:domain`) | (Properties only) Specifies the class to which a property applies. | `:hasUsername rdfs:domain :Player` |
| **Range** (`rdfs:range`) | (Properties only) Specifies the value type or class associated with a property. | `:hasUsername rdfs:range xsd:string` |
| **Other Axioms** | Captures logical constraints as structured XML comments to preserve modeling intent. | `<!-- Axiom: Disjoint with Game -->` (captured as comments) |

### Example output

```xml
<owl:Class rdf:about="http://www.semanticweb.org/myontology#Player">
  <!-- Axiom: disjointWith NPC -->
  <dc:source>CQ1, CQ3; HermiT: conflict; OOPS P10</dc:source>
  <vaem:rationale>
    [Logical Consistency Agent] Fixed subClassOf error;
    [Ontology Pitfall Agent] Added disjointness.
  </vaem:rationale>
  <!-- Axiom: disjointWith NPC -->
</owl:Class>

<owl:ObjectProperty rdf:about="http://www.semanticweb.org/myontology#triggersEvent">
  <rdfs:domain rdf:resource="http://www.semanticweb.org/myontology#Player"/>
  <rdfs:range rdf:resource="http://www.semanticweb.org/myontology#GameEvent"/>
  <dc:source>HermiT: introduced to resolve Player unsatisfiability</dc:source>
  <vaem:rationale>[Logical Consistency Agent] Created to correctly model player-event relationship.</vaem:rationale>
</owl:ObjectProperty>
```

---

## Evaluation

We evaluate MASEO framework across two complementary dimensions in three ontology generation case studies: Infrastructure Ontology, Vehicle Census Ontology (VCO), and Video Game Ontology (VGO).
1. **Structural characteristics & CQ coverage**: The first dimension combines structural analysis and CQ requirement coverage. Structural characteristics are derived from ontology diagrams, while CQ coverage is assessed from provenance records through expert inspection.
2. **Concept label matching & concept coverage**: The second dimension evaluates the alignment between concept labels in the generated ontologies and those in the corresponding gold-standard ontologies. We assess this alignment using three matching strategies, namely exact match, lexical match, and semantic match, and report precision, recall, F1-score, and concept coverage for each strategy.
## Datasets

| Dataset | Language | CQs | Gold Standard |
|---|---|---:|---|
| Infrastructure Ontology | Spanish | 5 | [Gold_Infrastructure.owl](https://github.com/oeg-upm/maseo/blob/main/dataset/gold_standard_ontology/Gold_Infrastructure.owl) |
| Vehicle Census Ontology (VCO) | Spanish | 28 | [Gold_VCO.owl](https://github.com/oeg-upm/maseo/blob/main/dataset/gold_standard_ontology/Gold_VCO.owl) |
| Video Game Ontology (VGO) | English | 68 | [Gold_VGO.owl](https://github.com/oeg-upm/maseo/blob/main/dataset/gold_standard_ontology/Gold_VGO.owl) |

## Evaluation Perspectives

### Structural Analysis

To compare the structural characteristics (e.g., number of classes, object properties, datatype properties, and hierarchy structure) for ontologies, visualization of the ontology is adopted to conduct the analysis. In this project, we have adopted `owl2diagram` to generate the diagrams.


### CQ Coverage

The proportion of input CQs that can be traced to at least one ontology element through provenance records. Therefore, we adopted CQ coverage to evaluate how many CQs are actually used in the ontology. Here is the calculation process of the CQ Coverage. 
```math
CQCoverage = \frac{|Q_{covered}|}{|Q_{input}|}
```

### Concept Label Matching

Concept label matching evaluates whether a concept label in the generated ontology can be aligned with a concept label in the corresponding gold-standard ontology.

To assess concept label alignment, we adopt three matching strategies:

- **Exact match**: labels are considered matched only when they are character-for-character identical.
- **Lexical match**: labels are matched based on character-level similarity using `SequenceMatcher` from the `difflib` library.
- **Semantic match**: labels are matched based on embedding cosine similarity using `embeddinggemma`, hosted locally via the Ollama runtime environment.


| Strategy | Method | Tool |
|---|---|---|
| Exact | String equality | — |
| Lexical | Character-level similarity | `difflib.SequenceMatcher` |
| Semantic | Embedding cosine similarity | `embeddinggemma` via Ollama |

The calculation process of Precision, recall, and F1-score is given here:

```math
P=\frac{TP}{TP+FP}, \quad
R=\frac{TP}{TP+FN}, \quad
F1=\frac{2PR}{P+R}
```

### Concept Coverage

To further evaluation for concept label mathcing, we adopted **Concept Coverage** to measure how many concepts in gold-standard ontology are matched.

Here is the calculation process for **Concept Coverage**
```math
ConceptCoverage^m = \frac{|C^m_{match}|}{|C_{gold}|}, \quad m \in \{exact, lex, sem\}
```

- `C_gold` is the set of gold-standard concepts
- `C_match^m` is the set of concepts matched under strategy `m`

## Execution

### Structural Analysis

Here is the command to generate the diagram for the generated/gold standard ontology:

```bash
python -m owl2diagram \
    dataset/gold_standard_ontology/Gold_VCO.owl \
    gold_VCO.md

python -m owl2diagram \
    dataset/generated_ontology/Gen_VCO.owl \
    gen_VCO.md
```

### Concept label matching

Here is the command to evaluate the generated ontology to the gold standard ontology. `generate_onto_file_path` refers to the local path to the generated ontology, `ground_onto_file_path` refers to the local path to the gold standard ontology.

```bash
cd evaluation
python eva_.py \
    --generate_onto_file_path ../dataset/generated_ontology/Gen_VCO.owl \
    --ground_onto_file_path   ../dataset/gold_standard_ontology/Gold_VCO.owl
```

## Result

### Structural Analysis

Here is an example of the result of  structural analysis: 

**Vehicle Census Ontology (VCO)**
Generated Ontology:
![VCO_gen](dataset/result/Structural_Analysis/Vehicle_Census/Gen_VCO.png)

Gold Standard Ontology:

![VCO_gold](dataset/result/Structural_Analysis/Vehicle_Census/Gold_VCO.png)

The full structural analysis of three ontologies:

| Element | Infrastructure (Gold / Gen) | VCO (Gold / Gen) | VGO (Gold / Gen) |
|---|---:|---:|---:|
| Classes | 37 / 14 | 7 / 15 | 37 / 13 |
| Object Properties | 13 / 12 | 4 / 18 | 32 / 33 |
| Datatype Properties | 0 / 5 | 4 / 2 | 6 / 9 |
| Subclass Relations | 15 / 7 | 1 / 4 | 24 / 0 |
| InverseOf Axioms | 0 / 6 | 0 / 9 | 0 / 15 |
| Linked CQs | 5 / 5 | 28 / 17 | 68 / 37 |
| CQ Coverage | 100.0% | 60.7% | 54.4% |

### CQ Coverage

| Dataset | Input CQs | Covered CQs | Coverage |
|---|---:|---:|---:|
| Infrastructure | 5 | 5 | 100.0% |
| Vehicle Census (VCO) | 28 | 17 | 60.7% |
| Video Game (VGO) | 68 | 37 | 54.4% |

### Class Counts Used for Concept Label Matching

| Dataset | Generated Classes | Gold-standard Classes |
|---|---:|---:|
| Infrastructure | 14 | 40 |
| Vehicle Census (VCO) | 15 | 10 |
| Video Game (VGO) | 13 | 37 |


### Concept Label Matching Results

| Dataset | Strategy | Precision | Recall | F1-score | Coverage |
|---|---|---:|---:|---:|---:|
| Infrastructure | Exact | 0.071 | 0.025 | 0.037 | 0.025 |
| Infrastructure | Lexical | 0.771 | 0.491 | 0.600 | 0.491 |
| Infrastructure | Semantic | 0.844 | 0.605 | 0.705 | 0.605 |
| Vehicle Census (VCO) | Exact | 0.267 | 0.444| 0.333 | 0.400 |
| Vehicle Census (VCO) | Lexical | 0.609 | 0.783 | 0.685 | 0.783|
| Vehicle Census (VCO) | Semantic | 0.711 | 0.846 | 0.772 | 0.846 |
| Video Game (VGO) | Exact | 0.385 | 0.135 | 0.200 | 0.135 |
| Video Game (VGO) | Lexical | 0.895 | 0.591 | 0.712 | 0.591|
| Video Game (VGO) | Semantic | 0.924 | 0.712 | 0.804 | 0.712 |
