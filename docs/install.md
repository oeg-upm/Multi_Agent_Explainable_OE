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
