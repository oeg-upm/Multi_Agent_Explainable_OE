# MEAONTO: Multi-Agent Framework for Explainable Ontology Generation

A fully automated, multi-agent pipeline that generates OWL ontologies directly from Competency Questions (CQs) and iteratively repairs them using external validation tools. Every ontology term produced by the pipeline is traceable to the agent and requirement that introduced it.

---

## Overview

This framework adopts a role-based multi-agent architecture with a built-in provenance tracking mechanism. Rather than producing a flat OWL file, the pipeline embeds a full modification history inside each ontology entity, recording which agent made each change and what motivated it.

The pipeline consists of four sequential stages:

| Agent | Model | Responsibility |
|-------|-------|----------------|
| `Ontology Generation Agent` | `deepseek-reasoner` | Generates the initial OWL ontology from CQs |
| `Syntax Repair Agent` | `deepseek-reasoner` | Fixes RDF/XML syntax errors reported by the parser |
| `Logical Consistency Agent` | `deepseek-reasoner` | Repairs logical inconsistencies reported by HermiT |
| `Pitfall Resolution Agent` | `deepseek-reasoner` | Resolves ontology modeling pitfalls reported by OOPS! |

![Multi-Agent Ontology Generation Pipeline](image/maseo_framework.png)

---

## Features

- **End-to-end automation** — from raw CQs to a validated OWL/RDF-XML ontology
- **Role-based agents** — each stage is handled by a dedicated LLM agent with a specific instruction and responsibility
- **Provenance tracking** — every ontology entity carries an append-only `vaem:rationale` log attributed to the agent that made each change, and a `dc:source` log linking each change back to the CQ, pitfall, or error that motivated it
- **Syntax self-loop** — syntax validation is re-applied after every repair stage until the ontology is well-formed
- **Structured output** — ontology entities are represented as typed Pydantic objects, ensuring schema conformance before serialisation to OWL/XML

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

### API key

This framework uses [DeepSeek](https://platform.deepseek.com/) as the LLM backend. Set your API key via the `--api_key` argument or as an environment variable:

```bash
export DEEPSEEK_API_KEY=your_api_key_here
```

---

## Configuration

Before running, update the following constants at the top of `agent_framework.py`:

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
  "What is the username of a player?"
]
```

---

## Ontology Entity Structure

Each generated ontology entity is a structured object with the following fields:

| Field | OWL Serialisation | Description |
|-------|-------------------|-------------|
| `Type` | XML tag | One of `owl:Class`, `owl:ObjectProperty`, `owl:DatatypeProperty` |
| `Name` | `rdf:about` | camelCase local name, combined with `BASE_URI` |
| `Comment` | `rdfs:comment` | Formal semantic definition |
| `Label` | `rdfs:label` | Human-readable identifier |
| `Rationale` | `vaem:rationale` | Append-only, agent-attributed modification log |
| `Source` | `dc:source` | Append-only log of CQs, pitfalls, or errors that motivated each change |
| `Domain` | `rdfs:domain` | Applicable to properties only |
| `Range` | `rdfs:range` | Applicable to properties only; XSD namespace used for datatype properties |
| `Functional` | `owl:FunctionalProperty` | Applicable to properties only |
| `Axiom` | `owl:Axiom` | Optional additional logical restriction |

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





