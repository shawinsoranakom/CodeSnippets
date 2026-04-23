def test_background_tasks():
    response = client.get("/context_b_bg")
    data = response.json()
    assert data["context_b"] == "started b"
    assert data["context_a"] == "started a"
    assert data["bg"] == "not set"
    middleware_state = json.loads(response.headers["x-state"])
    assert middleware_state["context_b"] == "started b"
    assert middleware_state["context_a"] == "started a"
    assert middleware_state["bg"] == "not set"
    assert state["context_b"] == "finished b with a: started a"
    assert state["context_a"] == "finished a"
    assert state["bg"] == "bg set - b: started b - a: started a"