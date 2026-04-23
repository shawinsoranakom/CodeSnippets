def test_body_validation_errors(self):
        body = {"variable": "FOO", "value": "BAZ"}
        chain = HandlerChain([OpenAPIRequestValidator()])
        request = Request(
            path="/_localstack/config",
            method="POST",
            body=json.dumps(body),
            scheme="http",
            headers={"Host": "localhost.localstack.cloud:4566", "Content-Type": "application/json"},
        )
        context = RequestContext(request)
        response = Response()
        chain.handle(context=context, response=response)
        assert response.status_code == 200

        # Request without the content type
        request.headers = {"Host": "localhost.localstack.cloud:4566"}
        context = RequestContext(request)
        response = Response()
        chain.handle(context=context, response=response)
        assert response.status_code == 400
        assert response.json["error"] == "Bad Request"
        assert response.json["message"] == "Request body validation error"

        # Request with invalid body
        context = RequestContext(
            Request(
                path="/_localstack/config",
                method="POST",
                body=json.dumps({"variable": "", "value": "BAZ"}),
                scheme="http",
                headers={
                    "Host": "localhost.localstack.cloud:4566",
                    "Content-Type": "application/json",
                },
            )
        )
        response = Response()
        chain.handle(context=context, response=response)
        assert response.status_code == 400
        assert response.json["error"] == "Bad Request"
        assert response.json["message"] == "Request body validation error"