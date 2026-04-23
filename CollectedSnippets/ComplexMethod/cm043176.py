def perform_completion_with_backoff(
    provider,
    prompt_with_variables,
    api_token,
    json_response=False,
    base_url=None,
    base_delay=2,
    max_attempts=3,
    exponential_factor=2,
    messages=None,
    **kwargs,
):
    """
    Perform an API completion request with exponential backoff.

    How it works:
    1. Sends a completion request to the API.
    2. Retries on rate-limit errors with exponential delays.
    3. Returns the API response or an error after all retries.

    Args:
        provider (str): The name of the API provider.
        prompt_with_variables (str): The input prompt for the completion request.
        api_token (str): The API token for authentication.
        json_response (bool): Whether to request a JSON response. Defaults to False.
        base_url (Optional[str]): The base URL for the API. Defaults to None.
        base_delay (int): The base delay in seconds. Defaults to 2.
        max_attempts (int): The maximum number of attempts. Defaults to 3.
        exponential_factor (int): The exponential factor. Defaults to 2.
        **kwargs: Additional arguments for the API request.

    Returns:
        dict: The API response or an error message after all retries.
    """

    from litellm import completion
    from litellm.exceptions import RateLimitError
    import litellm
    litellm.drop_params = True  # Auto-drop unsupported params (e.g., temperature for O-series/GPT-5)

    extra_args = {"temperature": 0.01, "api_key": api_token, "base_url": base_url}
    if json_response:
        extra_args["response_format"] = {"type": "json_object"}

    if kwargs.get("extra_args"):
        extra_args.update(kwargs["extra_args"])

    for attempt in range(max_attempts):
        try:
            response = completion(
                model=provider,
                messages=messages if messages is not None else [{"role": "user", "content": prompt_with_variables}],
                **extra_args,
            )
            return response  # Return the successful response
        except RateLimitError as e:
            print("Rate limit error:", str(e))

            if attempt == max_attempts - 1:
                # Last attempt failed, raise the error.
                raise

            # Check if we have exhausted our max attempts
            if attempt < max_attempts - 1:
                # Calculate the delay and wait
                delay = base_delay * (exponential_factor**attempt)  # Exponential backoff formula
                print(f"Waiting for {delay} seconds before retrying...")
                time.sleep(delay)
            else:
                # Return an error response after exhausting all retries
                return [
                    {
                        "index": 0,
                        "tags": ["error"],
                        "content": ["Rate limit error. Please try again later."],
                    }
                ]
        except Exception as e:
            raise e