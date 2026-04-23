def test_create_message():
    response = client.post("/messages", params={"input_message": "Hello"})
    assert response.status_code == 200, response.text
    assert response.json() == {
        "input": "Hello",
        "output": {"body": "Processed: Hello", "events": []},
    }