def test_streaming_with_hooks():
    """Test streaming endpoint with hooks"""
    print("\n" + "=" * 70)
    print("Testing: POST /crawl/stream with hooks")
    print("=" * 70)

    hooks_code = {
        "before_retrieve_html": """
async def hook(page, context, **kwargs):
    await page.evaluate("document.querySelectorAll('img').forEach(img => img.remove())")
    return page
"""
    }

    payload = {
        "urls": ["https://httpbin.org/html", "https://httpbin.org/json"],
        "hooks": {
            "code": hooks_code,
            "timeout": 10
        }
    }

    print("Sending streaming request with hooks...")

    with requests.post(f"{API_BASE_URL}/crawl/stream", json=payload, stream=True) as response:
        if response.status_code == 200:
            # Check headers for hooks status
            hooks_status = response.headers.get('X-Hooks-Status')
            if hooks_status:
                print(f"Hooks Status (from header): {hooks_status}")

            print("\nStreaming results:")
            for line in response.iter_lines():
                if line:
                    try:
                        result = json.loads(line)
                        if 'url' in result:
                            print(f"  Received: {result['url']}")
                        elif 'status' in result:
                            print(f"  Stream status: {result['status']}")
                    except json.JSONDecodeError:
                        print(f"  Raw: {line.decode()}")
        else:
            print(f"Error: {response.status_code}")