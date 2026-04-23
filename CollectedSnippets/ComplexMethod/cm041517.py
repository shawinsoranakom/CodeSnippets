def test_custom_endpoint(
        self, opensearch_wait_for_cluster, opensearch_create_domain, aws_client
    ):
        domain_name = f"opensearch-domain-{short_uid()}"
        custom_endpoint = "http://localhost:4566/my-custom-endpoint"
        domain_endpoint_options = {
            "CustomEndpoint": custom_endpoint,
            "CustomEndpointEnabled": True,
        }

        opensearch_create_domain(
            DomainName=domain_name, DomainEndpointOptions=domain_endpoint_options
        )

        response = aws_client.opensearch.describe_domain(DomainName=domain_name)
        response_domain_endpoint_options = response["DomainStatus"]["DomainEndpointOptions"]
        assert response_domain_endpoint_options["EnforceHTTPS"] is False
        assert response_domain_endpoint_options["TLSSecurityPolicy"]
        assert response_domain_endpoint_options["CustomEndpointEnabled"] is True
        assert response_domain_endpoint_options["CustomEndpoint"] == custom_endpoint

        response = aws_client.opensearch.list_domain_names(EngineType="OpenSearch")
        domain_names = [domain["DomainName"] for domain in response["DomainNames"]]

        assert domain_name in domain_names
        # wait for the cluster
        opensearch_wait_for_cluster(domain_name=domain_name)
        response = requests.get(f"{custom_endpoint}/_cluster/health")
        assert response.ok
        assert response.status_code == 200