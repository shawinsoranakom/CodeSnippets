def init_chat_model(
    model: str | None = None,
    *,
    model_provider: str | None = None,
    configurable_fields: Literal["any"] | list[str] | tuple[str, ...] | None = None,
    config_prefix: str | None = None,
    **kwargs: Any,
) -> BaseChatModel | _ConfigurableModel:
    """Initialize a chat model from any supported provider using a unified interface.

    **Two main use cases:**

    1. **Fixed model** – specify the model upfront and get a ready-to-use chat model.
    2. **Configurable model** – choose to specify parameters (including model name) at
        runtime via `config`. Makes it easy to switch between models/providers without
        changing your code

    !!! note "Installation requirements"

        Requires the integration package for the chosen model provider to be installed.

        See the `model_provider` parameter below for specific package names
        (e.g., `pip install langchain-openai`).

        Refer to the [provider integration's API reference](https://docs.langchain.com/oss/python/integrations/providers)
        for supported model parameters to use as `**kwargs`.

    Args:
        model: The model name, optionally prefixed with provider (e.g., `'openai:gpt-4o'`).

            Prefer exact model IDs from provider docs over aliases for reliable behavior
            (e.g., dated versions like `'...-20250514'` instead of `'...-latest'`).

            Will attempt to infer `model_provider` from model if not specified.

            The following providers will be inferred based on these model prefixes:

            - `gpt-...` | `o1...` | `o3...`       -> `openai`
            - `claude...`                         -> `anthropic`
            - `amazon...`                         -> `bedrock`
            - `gemini...`                         -> `google_vertexai`
            - `command...`                        -> `cohere`
            - `accounts/fireworks...`             -> `fireworks`
            - `mistral...`                        -> `mistralai`
            - `deepseek...`                       -> `deepseek`
            - `grok...`                           -> `xai`
            - `sonar...`                          -> `perplexity`
            - `solar...`                          -> `upstage`
        model_provider: The model provider if not specified as part of the model arg
            (see above).

            Supported `model_provider` values and the corresponding integration package
            are:

            - `openai`                  -> [`langchain-openai`](https://docs.langchain.com/oss/python/integrations/providers/openai)
            - `anthropic`               -> [`langchain-anthropic`](https://docs.langchain.com/oss/python/integrations/providers/anthropic)
            - `azure_openai`            -> [`langchain-openai`](https://docs.langchain.com/oss/python/integrations/providers/openai)
            - `azure_ai`                -> [`langchain-azure-ai`](https://docs.langchain.com/oss/python/integrations/providers/microsoft)
            - `google_vertexai`         -> [`langchain-google-vertexai`](https://docs.langchain.com/oss/python/integrations/providers/google)
            - `google_genai`            -> [`langchain-google-genai`](https://docs.langchain.com/oss/python/integrations/providers/google)
            - `anthropic_bedrock`       -> [`langchain-aws`](https://docs.langchain.com/oss/python/integrations/providers/aws)
            - `bedrock`                 -> [`langchain-aws`](https://docs.langchain.com/oss/python/integrations/providers/aws)
            - `bedrock_converse`        -> [`langchain-aws`](https://docs.langchain.com/oss/python/integrations/providers/aws)
            - `cohere`                  -> [`langchain-cohere`](https://docs.langchain.com/oss/python/integrations/providers/cohere)
            - `fireworks`               -> [`langchain-fireworks`](https://docs.langchain.com/oss/python/integrations/providers/fireworks)
            - `together`                -> [`langchain-together`](https://docs.langchain.com/oss/python/integrations/providers/together)
            - `mistralai`               -> [`langchain-mistralai`](https://docs.langchain.com/oss/python/integrations/providers/mistralai)
            - `huggingface`             -> [`langchain-huggingface`](https://docs.langchain.com/oss/python/integrations/providers/huggingface)
            - `groq`                    -> [`langchain-groq`](https://docs.langchain.com/oss/python/integrations/providers/groq)
            - `ollama`                  -> [`langchain-ollama`](https://docs.langchain.com/oss/python/integrations/providers/ollama)
            - `google_anthropic_vertex` -> [`langchain-google-vertexai`](https://docs.langchain.com/oss/python/integrations/providers/google)
            - `deepseek`                -> [`langchain-deepseek`](https://docs.langchain.com/oss/python/integrations/providers/deepseek)
            - `ibm`                     -> [`langchain-ibm`](https://docs.langchain.com/oss/python/integrations/providers/ibm)
            - `nvidia`                  -> [`langchain-nvidia-ai-endpoints`](https://docs.langchain.com/oss/python/integrations/providers/nvidia)
            - `xai`                     -> [`langchain-xai`](https://docs.langchain.com/oss/python/integrations/providers/xai)
            - `openrouter`              -> [`langchain-openrouter`](https://docs.langchain.com/oss/python/integrations/providers/openrouter)
            - `perplexity`              -> [`langchain-perplexity`](https://docs.langchain.com/oss/python/integrations/providers/perplexity)
            - `upstage`                 -> [`langchain-upstage`](https://docs.langchain.com/oss/python/integrations/providers/upstage)
            - `baseten`                 -> [`langchain-baseten`](https://docs.langchain.com/oss/python/integrations/providers/baseten)
            - `litellm`                 -> [`langchain-litellm`](https://docs.langchain.com/oss/python/integrations/providers/litellm)

        configurable_fields: Which model parameters are configurable at runtime:

            - `None`: No configurable fields (i.e., a fixed model).
            - `'any'`: All fields are configurable. **See security note below.**
            - `list[str] | Tuple[str, ...]`: Specified fields are configurable.

            Fields are assumed to have `config_prefix` stripped if a `config_prefix` is
            specified.

            If `model` is specified, then defaults to `None`.

            If `model` is not specified, then defaults to `("model", "model_provider")`.

            !!! warning "Security note"

                Setting `configurable_fields="any"` means fields like `api_key`,
                `base_url`, etc., can be altered at runtime, potentially redirecting
                model requests to a different service/user.

                Make sure that if you're accepting untrusted configurations that you
                enumerate the `configurable_fields=(...)` explicitly.

        config_prefix: Optional prefix for configuration keys.

            Useful when you have multiple configurable models in the same application.

            If `'config_prefix'` is a non-empty string then `model` will be configurable
            at runtime via the `config["configurable"]["{config_prefix}_{param}"]` keys.
            See examples below.

            If `'config_prefix'` is an empty string then model will be configurable via
            `config["configurable"]["{param}"]`.
        **kwargs: Additional model-specific keyword args to pass to the underlying
            chat model's `__init__` method. Common parameters include:

            - `temperature`: Model temperature for controlling randomness.
            - `max_tokens`: Maximum number of output tokens.
            - `timeout`: Maximum time (in seconds) to wait for a response.
            - `max_retries`: Maximum number of retry attempts for failed requests.
            - `base_url`: Custom API endpoint URL.
            - `rate_limiter`: A
                [`BaseRateLimiter`][langchain_core.rate_limiters.BaseRateLimiter]
                instance to control request rate.

            Refer to the specific model provider's
            [integration reference](https://reference.langchain.com/python/integrations/)
            for all available parameters.

    Returns:
        A `BaseChatModel` corresponding to the `model_name` and `model_provider`
            specified if configurability is inferred to be `False`. If configurable, a
            chat model emulator that initializes the underlying model at runtime once a
            config is passed in.

    Raises:
        ValueError: If `model_provider` cannot be inferred or isn't supported.
        ImportError: If the model provider integration package is not installed.

    ???+ example "Initialize a non-configurable model"

        ```python
        # pip install langchain langchain-openai langchain-anthropic langchain-google-vertexai

        from langchain.chat_models import init_chat_model

        o3_mini = init_chat_model("openai:o3-mini", temperature=0)
        claude_sonnet = init_chat_model("anthropic:claude-sonnet-4-5-20250929", temperature=0)
        gemini_2-5_flash = init_chat_model("google_vertexai:gemini-2.5-flash", temperature=0)

        o3_mini.invoke("what's your name")
        claude_sonnet.invoke("what's your name")
        gemini_2-5_flash.invoke("what's your name")
        ```

    ??? example "Partially configurable model with no default"

        ```python
        # pip install langchain langchain-openai langchain-anthropic

        from langchain.chat_models import init_chat_model

        # (We don't need to specify configurable=True if a model isn't specified.)
        configurable_model = init_chat_model(temperature=0)

        configurable_model.invoke("what's your name", config={"configurable": {"model": "gpt-4o"}})
        # Use GPT-4o to generate the response

        configurable_model.invoke(
            "what's your name",
            config={"configurable": {"model": "claude-sonnet-4-5-20250929"}},
        )
        ```

    ??? example "Fully configurable model with a default"

        ```python
        # pip install langchain langchain-openai langchain-anthropic

        from langchain.chat_models import init_chat_model

        configurable_model_with_default = init_chat_model(
            "openai:gpt-4o",
            configurable_fields="any",  # This allows us to configure other params like temperature, max_tokens, etc at runtime.
            config_prefix="foo",
            temperature=0,
        )

        configurable_model_with_default.invoke("what's your name")
        # GPT-4o response with temperature 0 (as set in default)

        configurable_model_with_default.invoke(
            "what's your name",
            config={
                "configurable": {
                    "foo_model": "anthropic:claude-sonnet-4-5-20250929",
                    "foo_temperature": 0.6,
                }
            },
        )
        # Override default to use Sonnet 4.5 with temperature 0.6 to generate response
        ```

    ??? example "Bind tools to a configurable model"

        You can call any chat model declarative methods on a configurable model in the
        same way that you would with a normal model:

        ```python
        # pip install langchain langchain-openai langchain-anthropic

        from langchain.chat_models import init_chat_model
        from pydantic import BaseModel, Field


        class GetWeather(BaseModel):
            '''Get the current weather in a given location'''

            location: str = Field(..., description="The city and state, e.g. San Francisco, CA")


        class GetPopulation(BaseModel):
            '''Get the current population in a given location'''

            location: str = Field(..., description="The city and state, e.g. San Francisco, CA")


        configurable_model = init_chat_model(
            "gpt-4o", configurable_fields=("model", "model_provider"), temperature=0
        )

        configurable_model_with_tools = configurable_model.bind_tools(
            [
                GetWeather,
                GetPopulation,
            ]
        )
        configurable_model_with_tools.invoke(
            "Which city is hotter today and which is bigger: LA or NY?"
        )
        # Use GPT-4o

        configurable_model_with_tools.invoke(
            "Which city is hotter today and which is bigger: LA or NY?",
            config={"configurable": {"model": "claude-sonnet-4-5-20250929"}},
        )
        # Use Sonnet 4.5
        ```

    """  # noqa: E501
    if model is not None and not isinstance(model, str):
        msg = (  # type: ignore[unreachable]
            f"`model` must be a string (e.g., 'openai:gpt-4o'), got "
            f"{type(model).__name__}. If you've already constructed a chat model "
            f"object, use it directly instead of passing it to init_chat_model()."
        )
        raise TypeError(msg)
    if not model and not configurable_fields:
        configurable_fields = ("model", "model_provider")
    config_prefix = config_prefix or ""
    if config_prefix and not configurable_fields:
        warnings.warn(
            f"{config_prefix=} has been set but no fields are configurable. Set "
            f"`configurable_fields=(...)` to specify the model params that are "
            f"configurable.",
            stacklevel=2,
        )

    if not configurable_fields:
        return _init_chat_model_helper(
            cast("str", model),
            model_provider=model_provider,
            **kwargs,
        )
    if model:
        kwargs["model"] = model
    if model_provider:
        kwargs["model_provider"] = model_provider
    return _ConfigurableModel(
        default_config=kwargs,
        config_prefix=config_prefix,
        configurable_fields=configurable_fields,
    )