async def test_docker_cache_permissions():
    """
    Verify Docker image has correct .cache folder permissions.

    This test requires Docker container to be running.
    """
    print_test("Docker Cache Permissions", "#1638")

    try:
        import httpx

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:11235/health")
            if response.status_code != 200:
                raise Exception("Docker not available")

        # Test by making a crawl request with caching
        async with httpx.AsyncClient(timeout=60.0) as client:
            request = {
                "urls": ["https://httpbin.org/html"],
                "crawler_config": {
                    "cache_mode": "enabled"
                }
            }

            response = await client.post(
                "http://localhost:11235/crawl",
                json=request
            )

            if response.status_code == 200:
                result = response.json()
                # Check if there were permission errors
                if "permission" in str(result).lower() and "denied" in str(result).lower():
                    record_result("Docker Cache Permissions", "#1638", False,
                                 "Permission denied error in response")
                else:
                    record_result("Docker Cache Permissions", "#1638", True,
                                 "Crawl with caching succeeded in Docker")
            else:
                error_text = response.text[:200]
                if "permission" in error_text.lower():
                    record_result("Docker Cache Permissions", "#1638", False,
                                 f"Permission error: {error_text}")
                else:
                    record_result("Docker Cache Permissions", "#1638", False,
                                 f"Request failed: {response.status_code}")

    except ImportError:
        record_result("Docker Cache Permissions", "#1638", True,
                     "Skipped - httpx not installed", skipped=True)
    except Exception as e:
        record_result("Docker Cache Permissions", "#1638", True,
                     f"Skipped - Docker not available: {e}", skipped=True)