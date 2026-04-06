def test_broken_session_data():
    with pytest.raises(ValueError, match="Session closed"):
        client.get("/broken-session-data")