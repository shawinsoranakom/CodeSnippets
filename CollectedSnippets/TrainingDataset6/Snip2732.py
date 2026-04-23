def test_generic_parameterless_depends():
    response = client.get("/a")
    assert response.status_code == 200, response.text
    assert response.json() == {"cls": "A"}

    response = client.get("/b")
    assert response.status_code == 200, response.text
    assert response.json() == {"cls": "B"}