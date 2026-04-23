def test_crud_health_check(self, echo_http_server_post, echo_http_server, aws_client):
        parsed_url = urlparse(echo_http_server_post)
        protocol = parsed_url.scheme.upper()
        host, _, port = parsed_url.netloc.partition(":")
        port = port or (443 if protocol == "HTTPS" else 80)
        path = (
            f"{parsed_url.path}health"
            if parsed_url.path.endswith("/")
            else f"{parsed_url.path}/health"
        )

        response = aws_client.route53.create_health_check(
            CallerReference=short_uid(),
            HealthCheckConfig={
                "FullyQualifiedDomainName": host,
                "Port": int(port),
                "ResourcePath": path,
                "Type": protocol,
                "RequestInterval": 10,
                "FailureThreshold": 2,
            },
        )
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 201
        health_check_id = response["HealthCheck"]["Id"]
        response = aws_client.route53.get_health_check(HealthCheckId=health_check_id)
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
        assert response["HealthCheck"]["Id"] == health_check_id
        response = aws_client.route53.delete_health_check(HealthCheckId=health_check_id)
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
        with pytest.raises(ClientError) as ctx:
            aws_client.route53.delete_health_check(HealthCheckId=health_check_id)
        assert "NoSuchHealthCheck" in str(ctx.value)