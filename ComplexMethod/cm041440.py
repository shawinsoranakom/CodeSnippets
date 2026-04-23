def test_multi_protocol_client_fixture(self, aws_cloudwatch_client):
        """
        Smoke test to validate that the client is indeed using the right protocol
        """
        response = aws_cloudwatch_client.describe_alarms()
        response_headers = response["ResponseMetadata"]["HTTPHeaders"]
        content_type = response_headers["content-type"]
        if aws_cloudwatch_client.test_client_protocol == "query":
            assert content_type in ("text/xml", "application/xml")
        elif aws_cloudwatch_client.test_client_protocol == "json":
            assert content_type == "application/x-amz-json-1.0"
        elif aws_cloudwatch_client.test_client_protocol == "smithy-rpc-v2-cbor":
            assert content_type == "application/cbor"
            assert response_headers["smithy-protocol"] == "rpc-v2-cbor"