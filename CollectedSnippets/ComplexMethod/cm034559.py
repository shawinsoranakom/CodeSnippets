def convert_markdown_to_html(content: str, token: Optional[str] = None) -> str:
    """Convert markdown to HTML using GitHub API with retry logic."""
    processed_content = process_markdown_links(content)

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Markdown-Converter/1.0"
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    payload = {
        "text": processed_content,
        "mode": "gfm",
        "context": "gpt4free/gpt4free"
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "https://api.github.com/markdown",
                json=payload,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                return response.text
            elif response.status_code == 403:
                print(f"Rate limit exceeded. Attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(60)
                continue
            elif response.status_code == 401:
                print("Authentication failed. Check your GITHUB_TOKEN.")
                sys.exit(1)
            else:
                print(f"API request failed with status {response.status_code}: {response.text}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                continue

        except requests.exceptions.RequestException as e:
            print(f"Network error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
            continue

    print("Failed to convert markdown after all retries")
    sys.exit(1)