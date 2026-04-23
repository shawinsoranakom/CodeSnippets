def test_invalid_hook():
    """Test with an invalid hook to see error handling"""
    print("\n" + "=" * 70)
    print("Testing: Invalid hook handling")
    print("=" * 70)

    # Intentionally broken hook
    hooks_code = {
        "on_page_context_created": """
def hook(page, context):  # Missing async!
    return page
""",

        "before_retrieve_html": """
async def hook(page, context, **kwargs):
    # This will cause an error
    await page.non_existent_method()
    return page
"""
    }

    payload = {
        "urls": ["https://httpbin.org/html"],
        "hooks": {
            "code": hooks_code,
            "timeout": 5
        }
    }

    print("Sending request with invalid hooks...")
    response = requests.post(f"{API_BASE_URL}/crawl", json=payload)

    if response.status_code == 200:
        data = response.json()

        if 'hooks' in data:
            hooks_info = data['hooks']
            print(f"\nHooks Status: {hooks_info['status']['status']}")

            if hooks_info['status']['validation_errors']:
                print("\n✅ Validation caught errors (as expected):")
                for error in hooks_info['status']['validation_errors']:
                    print(f"  - {error['hook_point']}: {error['error']}")

            if hooks_info['errors']:
                print("\n✅ Runtime errors handled gracefully:")
                for error in hooks_info['errors']:
                    print(f"  - {error['hook_point']}: {error['error']}")

            # The crawl should still succeed despite hook errors
            if data.get('success'):
                print("\n✅ Crawl succeeded despite hook errors (error isolation working!)")

    else:
        print(f"Error: {response.status_code}")
        print(response.text)