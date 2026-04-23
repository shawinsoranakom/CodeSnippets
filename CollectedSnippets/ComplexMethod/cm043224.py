def __init__(
        self,
        provider: str = DEFAULT_PROVIDER,
        api_token: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Optional[List[str]] = None,
        n: Optional[int] = None,
        backoff_base_delay: Optional[int] = None,
        backoff_max_attempts: Optional[int] = None,
        backoff_exponential_factor: Optional[int] = None,
    ):
        """Configuaration class for LLM provider and API token."""
        self.provider = provider
        if api_token and not api_token.startswith("env:"):
            self.api_token = api_token
        elif api_token and api_token.startswith("env:"):
            self.api_token = os.getenv(api_token[4:])
        else:
            # Check if given provider starts with any of key in PROVIDER_MODELS_PREFIXES
            # If not, check if it is in PROVIDER_MODELS
            prefixes = PROVIDER_MODELS_PREFIXES.keys()
            if any(provider.startswith(prefix) for prefix in prefixes):
                selected_prefix = next(
                    (prefix for prefix in prefixes if provider.startswith(prefix)),
                    None,
                )
                self.api_token = PROVIDER_MODELS_PREFIXES.get(selected_prefix)                    
            else:
                self.provider = DEFAULT_PROVIDER
                self.api_token = os.getenv(DEFAULT_PROVIDER_API_KEY)
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.stop = stop
        self.n = n
        self.backoff_base_delay = backoff_base_delay if backoff_base_delay is not None else 2
        self.backoff_max_attempts = backoff_max_attempts if backoff_max_attempts is not None else 3
        self.backoff_exponential_factor = backoff_exponential_factor if backoff_exponential_factor is not None else 2