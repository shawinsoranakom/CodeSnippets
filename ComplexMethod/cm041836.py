def fixed_litellm_completions(**params):
    """
    Just uses a dummy API key, since we use litellm without an API key sometimes.
    Hopefully they will fix this!
    """

    if "local" in params.get("model"):
        # Kinda hacky, but this helps sometimes
        params["stop"] = ["<|assistant|>", "<|end|>", "<|eot_id|>"]

    if params.get("model") == "i" and "conversation_id" in params:
        litellm.drop_params = (
            False  # If we don't do this, litellm will drop this param!
        )
    else:
        litellm.drop_params = True

    params["model"] = params["model"].replace(":latest", "")

    # Run completion
    attempts = 4
    first_error = None

    params["num_retries"] = 0

    for attempt in range(attempts):
        try:
            yield from litellm.completion(**params)
            return  # If the completion is successful, exit the function
        except KeyboardInterrupt:
            print("Exiting...")
            sys.exit(0)
        except Exception as e:
            if attempt == 0:
                # Store the first error
                first_error = e
            if (
                isinstance(e, litellm.exceptions.AuthenticationError)
                and "api_key" not in params
            ):
                print(
                    "LiteLLM requires an API key. Trying again with a dummy API key. In the future, if this fixes it, please set a dummy API key to prevent this message. (e.g `interpreter --api_key x` or `self.api_key = 'x'`)"
                )
                # So, let's try one more time with a dummy API key:
                params["api_key"] = "x"
            if attempt == 1:
                # Try turning up the temperature?
                params["temperature"] = params.get("temperature", 0.0) + 0.1

    if first_error is not None:
        raise first_error