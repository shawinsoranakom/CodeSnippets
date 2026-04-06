def test_exception_handler_body_access(client: TestClient):
    response = client.post("/", json={"numbers": [1, 2, 3]})
    assert response.json() == {
        "detail": {
            "errors": [
                {
                    "type": "list_type",
                    "loc": ["body"],
                    "msg": "Input should be a valid list",
                    "input": {"numbers": [1, 2, 3]},
                }
            ],
            # httpx 0.28.0 switches to compact JSON https://github.com/encode/httpx/issues/3363
            "body": IsOneOf('{"numbers": [1, 2, 3]}', '{"numbers":[1,2,3]}'),
        }
    }