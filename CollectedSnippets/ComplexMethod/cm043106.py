async def test_endpoint(
    session,
    endpoint: str,
    url: str,
    token: str,
    params: Optional[dict] = None,
    expected_status: int = 200
) -> Optional[dict]:
    """Test an endpoint with token and print results."""
    params = params or {}
    param_str = "&".join(f"{k}={v}" for k, v in params.items())
    full_url = f"http://localhost:8000/{endpoint}/{quote(url)}"
    if param_str:
        full_url += f"?{param_str}"

    headers = {"Authorization": f"Bearer {token}"}
    print(f"\nTesting: {full_url}")

    try:
        async with session.get(full_url, headers=headers) as response:
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
            assert status == expected_status, f"Expected {expected_status}, got {status}"
            return data
    except Exception as e:
        print(f"Error: {str(e)}")
        return None