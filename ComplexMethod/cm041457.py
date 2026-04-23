def test_put_events_to_target_api_destinations(
        self, httpserver: HTTPServer, auth, aws_client, clean_up
    ):
        token = short_uid()
        bearer = f"Bearer {token}"

        def _handler(_request: Request):
            return Response(
                json.dumps(
                    {
                        "access_token": token,
                        "token_type": "Bearer",
                        "expires_in": 86400,
                    }
                ),
                mimetype="application/json",
            )

        httpserver.expect_request("").respond_with_handler(_handler)
        http_endpoint = httpserver.url_for("/")

        if auth.get("type") == "OAUTH_CLIENT_CREDENTIALS":
            auth["parameters"]["AuthorizationEndpoint"] = http_endpoint

        connection_name = f"c-{short_uid()}"
        connection_arn = aws_client.events.create_connection(
            Name=connection_name,
            AuthorizationType=auth.get("type"),
            AuthParameters={
                auth.get("key"): auth.get("parameters"),
                "InvocationHttpParameters": {
                    "BodyParameters": [
                        {
                            "Key": "connection_body_param",
                            "Value": "value",
                            "IsValueSecret": False,
                        },
                    ],
                    "HeaderParameters": [
                        {
                            "Key": "connection-header-param",
                            "Value": "value",
                            "IsValueSecret": False,
                        },
                        {
                            "Key": "overwritten-header",
                            "Value": "original",
                            "IsValueSecret": False,
                        },
                    ],
                    "QueryStringParameters": [
                        {
                            "Key": "connection_query_param",
                            "Value": "value",
                            "IsValueSecret": False,
                        },
                        {
                            "Key": "overwritten_query",
                            "Value": "original",
                            "IsValueSecret": False,
                        },
                    ],
                },
            },
        )["ConnectionArn"]

        # create api destination
        dest_name = f"d-{short_uid()}"
        result = aws_client.events.create_api_destination(
            Name=dest_name,
            ConnectionArn=connection_arn,
            InvocationEndpoint=http_endpoint,
            HttpMethod="POST",
        )

        # create rule and target
        rule_name = f"r-{short_uid()}"
        target_id = f"target-{short_uid()}"
        pattern = json.dumps(
            {"source": ["source-123"], "detail-type": ["type-123"]}
        )  # TODO use standard defined event and pattern
        aws_client.events.put_rule(Name=rule_name, EventPattern=pattern)
        aws_client.events.put_targets(
            Rule=rule_name,
            Targets=[
                {
                    "Id": target_id,
                    "Arn": result["ApiDestinationArn"],
                    "Input": '{"target_value":"value"}',
                    "HttpParameters": {
                        "PathParameterValues": ["target_path"],
                        "HeaderParameters": {
                            "target-header": "target_header_value",
                            "overwritten_header": "changed",
                        },
                        "QueryStringParameters": {
                            "target_query": "t_query",
                            "overwritten_query": "changed",
                        },
                    },
                }
            ],
        )

        entries = [
            {
                "Source": "source-123",
                "DetailType": "type-123",
                "Detail": '{"i": 0}',
            }
        ]
        aws_client.events.put_events(Entries=entries)

        # Wait for event delivery before cleanup
        to_recv = 2 if auth["type"] == "OAUTH_CLIENT_CREDENTIALS" else 1
        assert poll_condition(lambda: len(httpserver.log) >= to_recv, timeout=5)

        event_request, _ = httpserver.log[-1]
        event = event_request.get_json(force=True)
        headers = event_request.headers
        query_args = event_request.args

        # Connection data validation
        assert event["connection_body_param"] == "value"
        assert headers["Connection-Header-Param"] == "value"
        assert query_args["connection_query_param"] == "value"

        # Target parameters validation
        assert "/target_path" in event_request.path
        assert event["target_value"] == "value"
        assert headers["Target-Header"] == "target_header_value"
        assert query_args["target_query"] == "t_query"

        # connection/target overwrite test
        assert headers["Overwritten-Header"] == "original"
        assert query_args["overwritten_query"] == "original"

        # Auth validation
        match auth["type"]:
            case "BASIC":
                user_pass = to_str(base64.b64encode(b"user:pass"))
                assert headers["Authorization"] == f"Basic {user_pass}"
            case "API_KEY":
                assert headers["Api"] == "apikey_secret"

            case "OAUTH_CLIENT_CREDENTIALS":
                assert headers["Authorization"] == bearer

                oauth_request, _ = httpserver.log[0]
                oauth_login = oauth_request.get_json(force=True)
                # Oauth login validation
                assert oauth_login["client_id"] == "id"
                assert oauth_login["client_secret"] == "password"
                assert oauth_login["oauthbody"] == "value1"
                assert oauth_request.headers["oauthheader"] == "value2"
                assert oauth_request.args["oauthquery"] == "value3"

        # Clean up after verification
        aws_client.events.delete_connection(Name=connection_name)
        aws_client.events.delete_api_destination(Name=dest_name)
        clean_up(rule_name=rule_name, target_ids=target_id)