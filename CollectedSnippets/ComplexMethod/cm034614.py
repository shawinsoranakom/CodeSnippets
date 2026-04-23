async def raise_for_status_async(response: Union[StreamResponse, ClientResponse], message: str = None):
    if response.ok:
        return
    is_html = False
    if message is None:
        content_type = response.headers.get("content-type", "")
        if content_type.startswith("application/json"):
            try:
                message = await response.json()
                if isinstance(message, list):
                    message = message[0] if message else {}
                error = message.get("error")
                if isinstance(error, dict):
                    message = error.get("message")
                else:
                    message = message.get("message", message)
                if isinstance(error, str):
                    message = f"{error}: {message}"
            except json.JSONDecodeError:
                message = await response.text()
        else:
            message = (await response.text()).strip()
            is_html = content_type.startswith("text/html") or message.lower().startswith("<!DOCTYPE".lower())
    if message is None or is_html:
        if response.status == 520:
            message = "Unknown error (Cloudflare)"
    if response.status in (429, 402):
        raise RateLimitError(f"Response {response.status}: {message}")
    if response.status == 401:
        raise MissingAuthError(f"Response {response.status}: {message}")
    if response.status == 403 and is_cloudflare(message):
        raise CloudflareError(f"Response {response.status}: Cloudflare detected")
    elif response.status == 403 and (is_openai(message) or is_lmarena(message)):
        raise MissingAuthError(f"Response {response.status}: OpenAI Bot detected")
    elif response.status == 502:
        raise ResponseStatusError(f"Response {response.status}: Bad Gateway")
    elif response.status == 504:
        raise RateLimitError(f"Response {response.status}: Gateway Timeout ")
    elif response.status == 400 and "API key not valid" in message:
        raise MissingAuthError(f"Response {response.status}: Invalid API key")
    else:
        raise ResponseStatusError(f"Response {response.status}: {'HTML content' if is_html else message}")