# MASEO: A Multi-Agent System for Explainable Ontology Generation


[![Documentation Status](https://readthedocs.org/projects/maseo/badge/?version=latest)](https://maseo.readthedocs.io/en/latest/?badge=latest)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19052004.svg)](https://doi.org/10.5281/zenodo.19052004) 
[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)


This repository provides the artifact for `MASEO`, a research-oriented multi-agent system that automated generate ontologies from competency questions, with a built-in focus on explainability. It aims to make the process of ontology generation more transparent, modular, and intelligent by distributing tasks among specialized agents. Each specialized agent is designed to keep track the logic behind each entity in generated ontology. 


### MASOE Structural Overview

The pipeline consists of four sequential stages:

| Agent | Model | Responsibility |
|-------|-------|----------------|
| `Ontology Generation Agent` | `deepseek-reasoner` | Generates the initial OWL ontology from CQs |
| `Syntax Repair Agent` | `deepseek-reasoner` | Fixes RDF/XML syntax errors reported by the parser |
| `Logical Consistency Agent` | `deepseek-reasoner` | Repairs logical inconsistencies reported by HermiT |
| `Pitfall Resolution Agent` | `deepseek-reasoner` | Resolves ontology modeling pitfalls reported by OOPS! |

The illustration of the MASOE framework:

<img src="docs/image/maseo_framework.png" alt="maseo overview" width="500">


### Features

- **End-to-end automation** — from a list of CQs to a validated ontology
- **Role-based agents** — each stage is handled by a dedicated LLM agent with a specific instruction and responsibility
- **Provenance tracking** — every ontology entity carries an append-only `vaem:rationale` log attributed to the agent that made each change, and a `dc:source` log linking each change back to the CQ, pitfall, or error that motivated it

---

## Installation

### Python dependencies

```bash
pip install agno rdflib requests beautifulsoup4 pydantic
```

### External tools requirements

| Tool | Purpose | Setup |
|------|---------|-------|
| [HermiT Reasoner](http://www.hermit-reasoner.com/) | Logical consistency checking | Download `HermiT.jar` and update the path in `reason_ontology()` |
| [OOPS! REST API](https://oops.linkeddata.es/) | Ontology pitfall detection | No local setup required — uses the public REST endpoint |
| Java (JRE 8+) | Required to run HermiT | `sudo apt install default-jre` |

### Configuration

<!-- 
Before running, update the following constants:

```bash
# Install java and ollama in you system
sudo apt update
sudo apt install deflault-jre
sudo apt install curl
curl -fsSL https://ollama.com/install.sh | sh
ollama pull embeddinggemma
ollama serve
```
-->
Make the changes in the `agent_framework.py` to ensure the correctness of variables. 
```python
# Path to your OOPS! request template
REQUEST_TEMPLATE = "src/templates/oops_request_template.xml"

# Path to HermiT JAR inside reason_ontology()
"java", "-jar", "/path/to/HermiT.jar"
```
### Execution Command Line

| Argument | Required | Description |
|----------|----------|-------------|
| `--api_key` | Yes | DeepSeek API key |
| `--cqs_file` | Yes | Path to a JSON file containing the list of competency questions |
| `--save_file` | Yes | Path where the final OWL ontology will be saved |
| `--agent_method` | No | `true` runs the full 4-stage pipeline; `false` runs generation only (default: `true`) |

```bash
python cli.py \
    --api_key      YOUR_DEEPSEEK_API_KEY \
    --cqs_file     dataset/competency_questions/VGO.json \
    --save_file    dataset/generated_ontology/Gen_VGO.owl \
    --agent_method true
```


### Input File Format

The input file that contains Competency Questions should be a JSON array of strings:

```json
{
  "CQ1": "What is the genre of a game?",
  "CQ2": "Which players have purchased an in-app item?",
  "CQ3": "What is the username of a player?",
...
}
```


### Output File Format
The internal representation and output format is available at our documentation [TBD]




## Acknowledgements

This work was supported by the grant [SOEL: Supporting Ontology Engineering with Large Language Models](https://w3id.org/soel) PID2023-152703NA-I00 funded by MCIN/AEI/10.13039/501100011033 and by ERDF/UE. The authors would also like to thank the EDINT (Espacios de Datos para las Infraestructuras Urbanas Inteligentes) ontology development team for sharing the project resources for evaluation purposes.

