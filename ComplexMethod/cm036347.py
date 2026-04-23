async def test_bootstrap_server(bootstrap_server: MooncakeBootstrapServer):
    """
    Tests the bootstrap server's api for worker registration and querying.

    Validates DP/TP/PP rank indexing and error handling for duplicate registrations.
    """

    import httpx

    base_url = f"http://127.0.0.1:{bootstrap_server.port}"

    # Query when empty
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/query")
        assert response.status_code == 200
        assert response.json() == {}

    # Register a worker
    payload1 = {
        "engine_id": "eng-1",
        "dp_rank": 0,
        "tp_rank": 0,
        "pp_rank": 0,
        "addr": "tcp://1.1.1.1:1111",
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{base_url}/register", json=payload1)
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    # Query after registration
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/query")
        assert response.status_code == 200
        data = response.json()
        assert "0" in data
        assert data["0"]["engine_id"] == "eng-1"
        assert data["0"]["worker_addr"]["0"]["0"] == "tcp://1.1.1.1:1111"

    # Test failure: re-registering the same worker
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{base_url}/register", json=payload1)
        assert response.status_code == 400
        assert "is already registered" in response.text

    # Test failure: engine_id mismatch for same dp_rank
    payload3_fail = {
        "engine_id": "eng-2",
        "dp_rank": 0,
        "tp_rank": 1,
        "pp_rank": 0,
        "addr": "tcp://3.3.3.3:3333",
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{base_url}/register", json=payload3_fail)
        assert response.status_code == 400
        assert "Engine ID mismatch" in response.text