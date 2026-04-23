async def test_credentials_with_complex_url_patterns(
        self,
        mock_requests_class,
        http_block,
        mock_response,
    ):
        """Test credentials matching various URL patterns."""
        # Test cases for different URL patterns
        test_cases = [
            {
                "host_pattern": "api.example.com",
                "test_url": "https://api.example.com/v1/users",
                "should_match": True,
            },
            {
                "host_pattern": "*.example.com",
                "test_url": "https://api.example.com/v1/users",
                "should_match": True,
            },
            {
                "host_pattern": "*.example.com",
                "test_url": "https://subdomain.example.com/data",
                "should_match": True,
            },
            {
                "host_pattern": "api.example.com",
                "test_url": "https://api.different.com/data",
                "should_match": False,
            },
        ]

        # Setup mocks
        mock_requests = AsyncMock()
        mock_requests.request.return_value = mock_response
        mock_requests_class.return_value = mock_requests

        for case in test_cases:
            # Reset mock for each test case
            mock_requests.reset_mock()

            # Create credentials for this test case
            test_creds = HostScopedCredentials(
                provider="http",
                host=case["host_pattern"],
                headers={
                    "Authorization": SecretStr(f"Bearer {case['host_pattern']}-token"),
                },
                title=f"Credentials for {case['host_pattern']}",
            )

            input_data = SendAuthenticatedWebRequestBlock.Input(
                url=case["test_url"],
                method=HttpMethod.GET,
                headers={"User-Agent": "test-agent"},
                credentials=cast(
                    HttpCredentials,
                    {
                        "id": test_creds.id,
                        "provider": "http",
                        "type": "host_scoped",
                        "title": test_creds.title,
                    },
                ),
            )

            # Execute with test credentials
            result = []
            async for output_name, output_data in http_block.run(
                input_data,
                credentials=test_creds,
                execution_context=make_test_context(),
            ):
                result.append((output_name, output_data))

            # Verify headers based on whether pattern should match
            mock_requests.request.assert_called_once()
            call_args = mock_requests.request.call_args
            headers = call_args.kwargs["headers"]

            if case["should_match"]:
                # Should include both user and credential headers
                expected_auth = f"Bearer {case['host_pattern']}-token"
                assert headers["Authorization"] == expected_auth
                assert headers["User-Agent"] == "test-agent"
            else:
                # Should only include user headers
                assert "Authorization" not in headers
                assert headers["User-Agent"] == "test-agent"