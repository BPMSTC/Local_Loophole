from __future__ import annotations

import json
from urllib import error, request


class LLMClient:
    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
        provider: str = "anthropic",
        base_url: str | None = None,
        api_key: str | None = None,
    ):
        self.model = model
        self.max_tokens = max_tokens
        self.provider = provider
        self.base_url = base_url.rstrip("/") if base_url else None
        self.api_key = api_key
        self.client = self._build_provider_client()

    def _build_provider_client(self):
        if self.provider == "anthropic":
            try:
                import anthropic
            except ImportError as exc:
                raise RuntimeError(
                    "The 'anthropic' package is required when model.provider is set to 'anthropic'."
                ) from exc
            return anthropic.Anthropic(api_key=self.api_key)

        if self.provider in {"ollama", "openai-compatible"}:
            return None

        raise ValueError(
            "Unsupported model provider. Use one of: anthropic, ollama, openai-compatible."
        )

    def call(self, system: str, user_message: str, temperature: float = 0.5) -> str:
        if self.provider == "anthropic":
            return self._call_anthropic(system, user_message, temperature)
        if self.provider == "ollama":
            return self._call_ollama(system, user_message, temperature)
        if self.provider == "openai-compatible":
            return self._call_openai_compatible(system, user_message, temperature)
        raise ValueError(f"Unsupported model provider: {self.provider}")

    def _call_anthropic(self, system: str, user_message: str, temperature: float) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text

    def _call_ollama(self, system: str, user_message: str, temperature: float) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_message},
            ],
            "options": {
                "temperature": temperature,
                "num_predict": self.max_tokens,
            },
        }
        response = self._post_json(f"{self._require_base_url()}/api/chat", payload)
        return response["message"]["content"]

    def _call_openai_compatible(self, system: str, user_message: str, temperature: float) -> str:
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_message},
            ],
        }
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        response = self._post_json(
            f"{self._require_base_url()}/chat/completions",
            payload,
            headers=headers,
        )
        return response["choices"][0]["message"]["content"]

    def _require_base_url(self) -> str:
        if not self.base_url:
            raise RuntimeError(
                f"model.base_url is required when model.provider is '{self.provider}'."
            )
        return self.base_url

    def _post_json(self, url: str, payload: dict, headers: dict | None = None) -> dict:
        request_headers = {
            "Content-Type": "application/json",
            **(headers or {}),
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(url, data=body, headers=request_headers, method="POST")

        try:
            with request.urlopen(req) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"LLM request failed with HTTP {exc.code}: {details}"
            ) from exc
        except error.URLError as exc:
            raise RuntimeError(
                f"Unable to reach model provider at {url}: {exc.reason}"
            ) from exc
