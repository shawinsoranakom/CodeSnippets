def download_test_file(url):
    """
    Download a URL to a local file, using hf_hub_download for HF URLs.

    For HuggingFace URLs, uses hf_hub_download which handles authentication
    automatically via the HF_TOKEN environment variable.

    Returns the local filename.
    """
    filename = url.split("/")[-1]

    # Skip if file already exists
    if os.path.exists(filename):
        print(f"File already exists: {filename}")
        return filename

    # Check if this is a HuggingFace URL
    hf_parts = parse_hf_url(url)

    if hf_parts:
        # Use hf_hub_download for HF URLs - handles auth automatically via HF_TOKEN env var
        print(f"Downloading {filename} from HuggingFace Hub...")
        try:
            hf_hub_download(**hf_parts, local_dir=".")
            print(f"Successfully downloaded: {filename}")
        except Exception as e:
            print(f"Error downloading {filename} from HuggingFace Hub: {e}")
            raise
    else:
        # Use httpx for non-HF URLs (COCO, Britannica, etc.)
        import time

        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Downloading {filename} from {url}")
                with open(filename, "wb") as f:
                    with httpx.stream("GET", url, follow_redirects=True) as resp:
                        resp.raise_for_status()
                        f.writelines(resp.iter_bytes(chunk_size=8192))

                validate_downloaded_content(filename)
                print(f"Successfully downloaded: {filename}")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    wait = 2 ** (attempt + 1)
                    print(f"Attempt {attempt + 1} failed for {filename}: {e}. Retrying in {wait}s...")
                    if os.path.exists(filename):
                        os.remove(filename)
                    time.sleep(wait)
                else:
                    raise

    return filename