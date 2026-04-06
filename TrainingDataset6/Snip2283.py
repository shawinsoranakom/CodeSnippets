def test_broken_no_raise():
    """
    When a dependency with yield raises after the yield (not in an except), the
    response is already "successfully" sent back to the client, but there's still
    an error in the server afterwards, an exception is raised and captured or shown
    in the server logs.
    """
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/broken")
        assert response.status_code == 200
        assert response.json() == {"message": "all good?"}