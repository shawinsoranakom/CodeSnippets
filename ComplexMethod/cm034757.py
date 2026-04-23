async def create_images(session: ClientSession, prompt: str, timeout: int = TIMEOUT_IMAGE_CREATION) -> List[str]:
    """
    Creates images based on a given prompt using Bing's service.

    Args:
        session (ClientSession): Active client session.
        prompt (str): Prompt to generate images.
        proxy (str, optional): Proxy configuration.
        timeout (int): Timeout for the request.

    Returns:
        List[str]: A list of URLs to the created images.

    Raises:
        RuntimeError: If image creation fails or times out.
    """
    if not has_requirements:
        raise MissingRequirementsError('Install "beautifulsoup4" package')
    url_encoded_prompt = quote(prompt)
    payload = f"q={url_encoded_prompt}&rt=4&FORM=GENCRE"
    url = f"{BING_URL}/images/create?q={url_encoded_prompt}&rt=4&FORM=GENCRE"
    async with session.post(url, allow_redirects=False, data=payload, timeout=timeout) as response:
        response.raise_for_status()
        text = (await response.text()).lower()
        if "0 coins available" in text:
            raise RateLimitError("No coins left. Log in with a different account or wait a while")
        for error in ERRORS:
            if error in text:
                raise RuntimeError(f"Create images failed: {error}")
    if response.status != 302:
        url = f"{BING_URL}/images/create?q={url_encoded_prompt}&rt=3&FORM=GENCRE"
        async with session.post(url, allow_redirects=False, timeout=timeout) as response:
            if response.status != 302:
                raise RuntimeError(f"Create images failed. Code: {response.status}")

    redirect_url = response.headers["Location"].replace("&nfy=1", "")
    redirect_url = f"{BING_URL}{redirect_url}"
    request_id = redirect_url.split("id=")[-1]
    async with session.get(redirect_url) as response:
        response.raise_for_status()

    polling_url = f"{BING_URL}/images/create/async/results/{request_id}?q={url_encoded_prompt}"
    start_time = time.time()
    while True:
        if time.time() - start_time > timeout:
            raise RuntimeError(f"Timeout error after {timeout} sec")
        async with session.get(polling_url) as response:
            if response.status != 200:
                raise RuntimeError(f"Polling images faild. Code: {response.status}")
            text = await response.text()
            if not text or "GenerativeImagesStatusPage" in text:
                await asyncio.sleep(1)
            else:
                break
    error = None
    try:
        error = json.loads(text).get("errorMessage")
    except Exception:
        pass
    if error == "Pending":
        raise RuntimeError("Prompt is been blocked")
    elif error:
        raise RuntimeError(error)
    return read_images(text)