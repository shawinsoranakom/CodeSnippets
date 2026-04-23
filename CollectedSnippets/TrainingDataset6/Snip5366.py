def test_union_body_discriminator_annotated(client: TestClient) -> None:
    response = client.post("/pet/annotated", json={"pet_type": "dog", "barks": 3.5})
    assert response.status_code == 200, response.text
    assert response.json() == {"pet_type": "dog", "barks": 3.5}