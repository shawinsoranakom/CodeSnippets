def total_token_count_from_response(resp):
    """
    Extract token count from LLM response in various formats.

    Handles None responses and different response structures from various LLM providers.
    Returns 0 if token count cannot be determined.
    """
    if resp is None:
        return 0

    try:
        if hasattr(resp, "usage") and hasattr(resp.usage, "total_tokens"):
            return resp.usage.total_tokens
    except Exception:
        pass

    try:
        if hasattr(resp, "usage_metadata") and hasattr(resp.usage_metadata, "total_tokens"):
            return resp.usage_metadata.total_tokens
    except Exception:
        pass

    try:
        if hasattr(resp, "meta") and hasattr(resp.meta, "billed_units") and hasattr(resp.meta.billed_units, "input_tokens"):
            return resp.meta.billed_units.input_tokens
    except Exception:
        pass

    if isinstance(resp, dict) and 'usage' in resp and 'total_tokens' in resp['usage']:
        try:
            return resp["usage"]["total_tokens"]
        except Exception:
            pass

    if isinstance(resp, dict) and 'usage' in resp and 'input_tokens' in resp['usage'] and 'output_tokens' in resp['usage']:
        try:
            return resp["usage"]["input_tokens"] + resp["usage"]["output_tokens"]
        except Exception:
            pass

    if isinstance(resp, dict) and 'meta' in resp and 'tokens' in resp['meta'] and 'input_tokens' in resp['meta']['tokens'] and 'output_tokens' in resp['meta']['tokens']:
        try:
            return resp["meta"]["tokens"]["input_tokens"] + resp["meta"]["tokens"]["output_tokens"]
        except Exception:
            pass
    return 0