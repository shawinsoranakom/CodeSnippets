def test_union_body_discriminator_assignment(client: TestClient) -> None:
    response = client.post("/pet/assignment", json={"pet_type": "cat", "meows": 5})
    assert response.status_code == 200, response.text
    assert response.json() == {"pet_type": "cat", "meows": 5}