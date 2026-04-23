def raise_for_status(response: Union[Response, StreamResponse, ClientResponse, RequestsResponse], message: str = None):
    if hasattr(response, "status"):
        return raise_for_status_async(response, message)
    if response.ok:
        return
    is_html = False
    if message is None:
        is_html = response.headers.get("content-type", "").startswith("text/html") or response.text.startswith("<!DOCTYPE")
        message = response.text
    if message is None or is_html:
        if response.status_code == 520:
            message = "Unknown error (Cloudflare)"
    if response.status_code in (429, 402):
        raise RateLimitError(f"Response {response.status_code}: {message}")
    if response.status_code == 401:
        raise MissingAuthError(f"Response {response.status_code}: {message}")
    if response.status_code == 403 and is_cloudflare(response.text):
        raise CloudflareError(f"Response {response.status_code}: Cloudflare detected")
    elif response.status_code == 403 and is_openai(response.text):
        raise MissingAuthError(f"Response {response.status_code}: OpenAI Bot detected")
    elif response.status_code == 502:
        raise ResponseStatusError(f"Response {response.status_code}: Bad Gateway")
    elif response.status_code == 504:
        raise RateLimitError(f"Response {response.status_code}: Gateway Timeout ")
    elif response.status_code == 400 and "API key not valid" in message:
        raise MissingAuthError(f"Response {response.status_code}: Invalid API key")
    else:
        raise ResponseStatusError(f"Response {response.status_code}: {'HTML content' if is_html else message}")