# Configuration

All MASEO behaviour is controlled by a single YAML file, which covers model selection, agent instructions, prompts and relative path for ontology tools.

## Configuration YAML Structure

```yaml
ontology:
  base_uri: "http://www.semanticweb.org/myontology#"

model:
  provider: "openrouter"
  max_tokens: 16384
  temperature: 0.0
  ollama:    
    id: "..."
  deepseek:
    id: "..." 
    api_key: "..."
  openrouter:
    id: "..."
    api_key: "..."

agents:
  default_retries: 3

oops:
  api_url: "https://oops.linkeddata.es/rest"
  request_template: "./templates/oops_request_template.xml"

hermit:
  jar_path: "./hermit/HermiT.jar"

prompts:
  ontology_generation:
    name: "Ontology Generation Agent"
    role: "Ontology specialist"
    instruction: |
        You are an experienced knowledge engineer modelling a specific domain....
    prompt_template: |
        All competency questions are provided here: {competency_questions}...
  syntax_repair:          ... 
  logical_consistency:    ... 
  pitfall_resolution:     ... 
```

Relative paths in `oops.request_template` and `hermit.jar_path` are resolved against the directory containing `config.yaml`.

## Ontology Information

| Key | Type | Description |
| --- | --- | --- |
| `base_uri` | string | The base URI used for every generated entity. |

## LLM Model Information

The `provider` key selects which subsection is active. Other subsections are ignored.

| Key | Type | Description |
| --- | --- | --- |
| `provider` | string | One of `ollama`, `deepseek`, `openrouter`. |
| `max_tokens` | int | Cap on generated tokens per call. Shared across providers; per-provider override allowed. |
| `temperature` | float | Sampling temperature. `0.0` is fully deterministic. |


## Agent

| Key | Type | Description |
| --- | --- | --- |
| `default_retries` | int | Number of full pipeline restarts allowed before MASEO gives up. Each unrecoverable error consumes one retry. |

## OOPS

| Key | Type | Description |
| --- | --- | --- |
| `api_url` | string | OOPS! REST endpoint. The default is the public one. |
| `request_template` | path | XML template used to build the OOPS! request body. The default template at `./templates/oops_request_template.xml` is suitable for most users. |

## HermiT

| Key | Type | Description |
| --- | --- | --- |
| `jar_path` | path | Path to `HermiT.jar`. Relative to the config file. |

## `prompts`

Each of the four agents has its own block under `prompts`:

| Key | Description |
| --- | --- |
| `name` | Display name passed to `agno.Agent`. e.g., `Ontology Generation Agent` |
| `role` | Short role string, e.g., `Ontology specialist` |
| `instructions` | System-level instructions as the intention of the agent. Set once per agent. |
| `prompt_template` | The user message sent on every call. May include placeholders specific to that agent. |

