def test_custom_endpoint_disabled(
        self, opensearch_wait_for_cluster, opensearch_create_domain, aws_client
    ):
        domain_name = f"opensearch-domain-{short_uid()}"
        domain_endpoint_options = {
            "CustomEndpointEnabled": False,
        }

        opensearch_create_domain(
            DomainName=domain_name, DomainEndpointOptions=domain_endpoint_options
        )

        response = aws_client.opensearch.describe_domain(DomainName=domain_name)
        response_domain_name = response["DomainStatus"]["DomainName"]
        assert domain_name == response_domain_name

        response_domain_endpoint_options = response["DomainStatus"]["DomainEndpointOptions"]
        assert response_domain_endpoint_options["EnforceHTTPS"] is False
        assert response_domain_endpoint_options["TLSSecurityPolicy"]
        assert response_domain_endpoint_options["CustomEndpointEnabled"] is False
        assert "CustomEndpoint" not in response_domain_endpoint_options

        endpoint = f"http://{response['DomainStatus']['Endpoint']}"

        # wait for the cluster
        opensearch_wait_for_cluster(domain_name=domain_name)
        response = requests.get(f"{endpoint}/_cluster/health")
        assert response.ok
        assert response.status_code == 200