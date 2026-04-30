# Install

## Requirements

- Python 3.10
- OpenJKD 11
  
### External Requirements Usage:

| Tool | Purpose | Setup |
|------|---------|-------|
| [HermiT Reasoner](http://www.hermit-reasoner.com/) | Logical consistency checking | Download `HermiT.jar` |
| [OOPS! REST API](https://oops.linkeddata.es/) | Ontology pitfall detection | No local setup required — uses the public REST endpoint |
| Java (JRE 8+) | Required to run HermiT | `sudo apt install default-jre` |


## Install from Github

To run MASEO project, please see the following steps:

1. Clone the source code:
```bash
git clone https://github.com/oeg-upm/maseo.git
```
2. Install the python dependencies:
```bash
# thought poetry to manage the env
poetry install
source .venv/bin/activate
# direct install from pypi
pip install agno rdflib requests beautifulsoup4 pydantic fastapi uvicorn
```
3. To test the MASEO pipeline, run:
```bash

cd src/maseo/ # enter the source code folder
python -u cli.py \
--config ./config.yaml \
--cqs_file ./dataset/cqs/wine_cqs.json \
--save_file ./dataset/agent/gemma4-26b/ontology/wine_ontology.owl \
--agent_method true 2>&1 | tee ./dataset/agent/gemma4-26b/log/wine_cq2onto_log.txt
```

cli.py arguments:

| Argument | Required | Description |
|----------|----------|-------------|
| `--api_key` | Yes | DeepSeek API key |
| `--cqs_file` | Yes | Path to a JSON file containing the list of competency questions |
| `--save_file` | Yes | Path where the final OWL ontology will be saved |
| `--agent_method` | No | `true` runs the full 4-stage pipeline; `false` runs generation only (default: `true`) |

