def test_broken_raise():
    with pytest.raises(ValueError, match="Broken after yield"):
        client.get("/broken")