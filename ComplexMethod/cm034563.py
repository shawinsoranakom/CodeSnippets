def generate_commit_message(diff_text: str, model: str = DEFAULT_MODEL, max_retries: int = MAX_RETRIES) -> Optional[str]:
    """Generate a commit message based on the git diff"""
    if not diff_text or diff_text.strip() == "":
        return "No changes staged for commit"

    read_cookie_files()  # Load cookies for g4f client

    # Filter sensitive data
    filtered_diff = filter_sensitive_data(diff_text)

    # Truncate if necessary
    truncated_diff = truncate_diff(filtered_diff)

    client = Client()

    prompt = f"""
    {truncated_diff}
    ```

    Analyze ONLY the exact changes in this git diff and create a precise commit message.

    FORMAT:
    1. First line: "<type>: <summary>" (max 70 chars)
       - Type: feat, fix, docs, refactor, test, etc.
       - Summary must describe ONLY actual changes shown in the diff

    2. Leave one blank line

    3. Add sufficient bullet points to:
       - Describe ALL specific changes seen in the diff
       - Reference exact functions/files/components that were modified
       - Do NOT mention anything not explicitly shown in the code changes
       - Avoid general statements or assumptions not directly visible in diff
       - Include enough points to cover all significant changes (don't limit to a specific number)

    IMPORTANT: Be 100% factual. Only mention code that was actually changed. Never invent or assume changes not shown in the diff. If unsure about a change's purpose, describe what changed rather than why. Output nothing except for the commit message, and don't surround it in quotes.
    """

    for attempt in range(max_retries):
        try:
            # Start spinner
            spinner = show_spinner()

            # Make API call
            response = client.chat.completions.create(
                prompt,
                model=model,
                stream=True,
            )
            content = []
            for chunk in response:
                if isinstance(chunk.choices[0].delta.content, str):
                    # Stop spinner and clear line
                    if spinner:
                        spinner.set()
                        print(" " * 50 + "\n", flush=True)
                        spinner = None
                    content.append(chunk.choices[0].delta.content)
                    print(chunk.choices[0].delta.content, end="", flush=True)
            return "".join(content).strip("`").split("\n---\n")[0].strip()
        except Exception as e:
            # Stop spinner if it's running
            if 'spinner' in locals() and spinner:
                spinner.set()
                sys.stdout.write("\r" + " " * 50 + "\r")
                sys.stdout.flush()
            if max_retries == 1:
                raise e  # If no retries, raise immediately
            print(f"Error generating commit message (attempt {attempt+1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                print(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
                # Try with a fallback model if available
                if attempt < len(FALLBACK_MODELS):
                    fallback = FALLBACK_MODELS[attempt]
                    print(f"Trying with fallback model: {fallback}")
                    model = fallback

    return None