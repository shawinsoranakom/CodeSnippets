def test_host_prefix_no_subdomain(
        self,
    ):
        """This tests help to detect any potential future new host prefix domains added to the botocore specs.
        If this test fails:
        1) Add the new entry to `HOST_PREFIXES_NO_SUBDOMAIN` to reflect any changes
        2) IMPORTANT: Add a public DNS entry for the given host prefix!
        """
        unique_prefixes = set()
        for service_model, operation in iterate_service_operations():
            if operation.endpoint and operation.endpoint.get("hostPrefix"):
                unique_prefixes.add(operation.endpoint["hostPrefix"])

        non_dot_unique_prefixes = [prefix for prefix in unique_prefixes if not prefix.endswith(".")]
        # Intermediary validation to easily summarize all differences
        assert set(HOST_PREFIXES_NO_SUBDOMAIN) == set(non_dot_unique_prefixes)

        # Real validation of NAME_PATTERNS_POINTING_TO_LOCALSTACK
        for host_prefix in non_dot_unique_prefixes:
            assert f"{host_prefix}{LOCALHOST_HOSTNAME}" in NAME_PATTERNS_POINTING_TO_LOCALSTACK