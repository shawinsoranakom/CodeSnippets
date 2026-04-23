async def test_endpoint(
    endpoint: str, 
    url: str, 
    params: Optional[dict] = None,
    expected_status: int = 200
) -> None:
    """Test an endpoint and print results"""
    import aiohttp

    params = params or {}
    param_str = "&".join(f"{k}={v}" for k, v in params.items())
    full_url = f"http://localhost:8000/{endpoint}/{quote(url)}"
    if param_str:
        full_url += f"?{param_str}"

    print(f"\nTesting: {full_url}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(full_url) as response:
                status = response.status
                try:
                    data = await response.json()
                except:
                    data = await response.text()

                print(f"Status: {status} (Expected: {expected_status})")
                if isinstance(data, dict):
                    print(f"Response: {json.dumps(data, indent=2)}")
                else:
                    print(f"Response: {data[:500]}...")  # First 500 chars
                assert status == expected_status
                return data
    except Exception as e:
        print(f"Error: {str(e)}")
        return None