def test_authentication_hook():
    """Test authentication using hooks"""
    print("\n" + "=" * 70)
    print("Testing: Authentication with hooks")
    print("=" * 70)

    hooks_code = {
        "before_goto": """
async def hook(page, context, url, **kwargs):
    # For httpbin.org basic auth test, set Authorization header
    import base64

    # httpbin.org/basic-auth/user/passwd expects username="user" and password="passwd"
    credentials = base64.b64encode(b"user:passwd").decode('ascii')

    await page.set_extra_http_headers({
        'Authorization': f'Basic {credentials}'
    })

    print(f"Hook: Set Authorization header for {url}")
    return page
""",
        "on_page_context_created": """
async def hook(page, context, **kwargs):
    # Example: Add cookies for session tracking
    await context.add_cookies([
        {
            'name': 'session_id',
            'value': 'test_session_123',
            'domain': '.httpbin.org',
            'path': '/',
            'httpOnly': True,
            'secure': True
        }
    ])

    print("Hook: Added session cookie")
    return page
"""
    }

    payload = {
        "urls": ["https://httpbin.org/basic-auth/user/passwd"],
        "hooks": {
            "code": hooks_code,
            "timeout": 30
        }
    }

    print("Sending request with authentication hook...")
    response = requests.post(f"{API_BASE_URL}/crawl", json=payload)

    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("✅ Crawl with authentication hook successful")

            # Check if hooks executed
            if 'hooks' in data:
                hooks_info = data['hooks']
                if hooks_info.get('summary', {}).get('successful', 0) > 0:
                    print(f"✅ Authentication hooks executed: {hooks_info['summary']['successful']} successful")

                # Check for any hook errors
                if hooks_info.get('errors'):
                    print("⚠️ Hook errors:")
                    for error in hooks_info['errors']:
                        print(f"  - {error}")

            # Check if authentication worked by looking at the result
            if 'results' in data and len(data['results']) > 0:
                result = data['results'][0]
                if result.get('success'):
                    print("✅ Page crawled successfully (authentication worked!)")
                    # httpbin.org/basic-auth returns JSON with authenticated=true when successful
                    if 'authenticated' in str(result.get('html', '')):
                        print("✅ Authentication confirmed in response content")
                else:
                    print(f"❌ Crawl failed: {result.get('error_message', 'Unknown error')}")
        else:
            print("❌ Request failed")
            print(f"Response: {json.dumps(data, indent=2)}")
    else:
        print(f"❌ Error: {response.status_code}")
        try:
            error_data = response.json()
            print(f"Error details: {json.dumps(error_data, indent=2)}")
        except:
            print(f"Error text: {response.text[:500]}")