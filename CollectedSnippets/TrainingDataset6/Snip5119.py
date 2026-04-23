def test_path_operation(client: TestClient):
    expected_content = """<?xml version="1.0"?>
    <shampoo>
    <Header>
        Apply shampoo here.
    </Header>
    <Body>
        You'll have to use soap here.
    </Body>
    </shampoo>
    """

    response = client.get("/legacy/")
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/xml"
    assert response.text == expected_content