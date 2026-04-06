def test_with_computed_field():
    client = get_app_client()
    client_no = get_app_client(separate_input_output_schemas=False)
    response = client.post("/with-computed-field/", json={"name": "example"})
    response2 = client_no.post("/with-computed-field/", json={"name": "example"})
    assert response.status_code == response2.status_code == 200, response.text
    assert (
        response.json()
        == response2.json()
        == {
            "name": "example",
            "computed_field": "computed example",
        }
    )