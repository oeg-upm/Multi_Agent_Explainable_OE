import os
from pathlib import Path
from typing import Any, Dict

import yaml

 

class Config:
 
    def __init__(self, raw: Dict[str, Any], config_dir: Path):
        self._raw = raw
        self._config_dir = config_dir
 
        self.base_uri: str = raw["ontology"]["base_uri"]
 
        self.model_provider: str = raw["model"]["provider"].lower().strip()
        self.model_cfg: Dict[str, Any] = raw["model"].get(self.model_provider, {}) or {}
 
        if "id" not in self.model_cfg:
            raise ValueError(
                f"Model provider '{self.model_provider}' is missing the required 'id' field in config."
            )
        self.model_id: str = self.model_cfg["id"]
 
        self.default_retries: int = int(raw["agents"]["default_retries"])
 
        oops_cfg = raw["oops"]
        self.oops_api_url: str = oops_cfg["api_url"]
        self.oops_request_template: Path = self._resolve_path(oops_cfg["request_template"])
 
        hermit_cfg = raw["hermit"]
        self.hermit_jar: Path = self._resolve_path(hermit_cfg["jar_path"])
 
 
        self.prompts: Dict[str, Dict[str, str]] = raw["prompts"]
 
    def _resolve_path(self, path_str: str) -> Path:
        p = Path(path_str).expanduser()
        if p.is_absolute():
            return p
        return (self._config_dir / p).resolve()
 
    def get_api_key(self) -> str | None:
        if self.model_provider == "deepseek":
            return os.environ.get("DEEPSEEK_API_KEY") or self.model_cfg["api_key"] or None
        return None
 
    def prompt(self, agent_key: str) -> Dict[str, str]:
        if agent_key not in self.prompts:
            raise KeyError(f"No prompt defined for agent '{agent_key}' in config.yaml")
        return self.prompts[agent_key]
 
    def render_prompt(self, agent_key: str, **kwargs: Any) -> str:
        block = self.prompt(agent_key)
        template = block["prompt_template"]
        if not template:
            raise KeyError(
                f"Agent '{agent_key}' has no `prompt_template` defined in config.yaml."
            )
        try:
            return template.format(**kwargs)
        except KeyError as missing:
            raise KeyError(
                f"Prompt template for '{agent_key}' references placeholder "
                f"{missing} but it was not provided. Supplied keys: {list(kwargs)}"
            ) from missing
 
 
def load_config(path: str | os.PathLike) -> Config:
    config_path = Path(path).expanduser().resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
 
    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
 
    return Config(raw, config_dir=config_path.parent)
 