import os

from config import Config


def build_model(config: Config):
    provider = config.model_provider

    if provider == "ollama":
        from agno.models.ollama import Ollama

        kwargs = {"id": config.model_id}
        host = config.model_cfg.get("host")
        if host:
            kwargs["host"] = host
        return Ollama(**kwargs)

    if provider == "deepseek":
        from agno.models.deepseek import DeepSeek

        api_key = config.get_api_key()
        if api_key:
            # DeepSeek SDK reads DEEPSEEK_API_KEY from env
            os.environ["DEEPSEEK_API_KEY"] = api_key

        kwargs = {"id": config.model_id}
        base_url = config.model_cfg.get("base_url")
        if base_url:
            kwargs["base_url"] = base_url
        return DeepSeek(**kwargs)

    raise ValueError(
        f"Unsupported model provider: '{provider}'. "
        f"Supported providers: 'ollama', 'deepseek'."
    )
