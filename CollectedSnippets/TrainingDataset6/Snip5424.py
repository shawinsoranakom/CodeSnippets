def test_wrapped_method_type_inference():
    """
    Regression test ensuring that when a method imported from another module
    is decorated with something that sets the __wrapped__ attribute (functools.wraps),
    then the types are still processed correctly, including dereferencing of forward
    references.
    """
    app = FastAPI()
    client = TestClient(app)
    app.post("/endpoint")(passthrough(forwardref_method))
    app.post("/endpoint2")(passthrough(passthrough(forwardref_method)))
    with client:
        response = client.post("/endpoint", json={"input": {"x": 0}})
        response2 = client.post("/endpoint2", json={"input": {"x": 0}})
    assert response.json() == response2.json() == {"x": 1}