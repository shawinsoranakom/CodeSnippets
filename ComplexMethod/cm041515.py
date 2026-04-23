def test_security_plugin(self, opensearch_create_domain, aws_client):
        master_user_auth = ("master-user", "1[D3&2S)u9[G")

        # enable the security plugin for this test
        advanced_security_options = AdvancedSecurityOptionsInput(
            Enabled=True,
            InternalUserDatabaseEnabled=True,
            MasterUserOptions=MasterUserOptions(
                MasterUserName=master_user_auth[0],
                MasterUserPassword=master_user_auth[1],
            ),
        )
        domain_name = opensearch_create_domain(AdvancedSecurityOptions=advanced_security_options)
        endpoint = aws_client.opensearch.describe_domain(DomainName=domain_name)["DomainStatus"][
            "Endpoint"
        ]

        # make sure the plugins are installed (Sort and display component)
        plugins_url = f"https://{endpoint}/_cat/plugins?s=component&h=component"

        # request without credentials fails
        unauthorized_response = requests.get(plugins_url, headers={"Accept": "application/json"})
        assert unauthorized_response.status_code == 401

        # request with default admin credentials is successful
        plugins_response = requests.get(
            plugins_url, headers={"Accept": "application/json"}, auth=master_user_auth
        )
        assert plugins_response.status_code == 200
        installed_plugins = {plugin["component"] for plugin in plugins_response.json()}
        assert "opensearch-security" in installed_plugins

        # create a new index with the admin user
        test_index_name = "new-index"
        test_index_id = "new-index-id"
        test_document = {"test-key": "test-value"}
        admin_client = OpenSearch(hosts=endpoint, http_auth=master_user_auth)
        admin_client.create(index=test_index_name, id=test_index_id, body={})
        admin_client.index(index=test_index_name, body=test_document)

        # create a new "readall" rolemapping
        test_rolemapping = {"backend_roles": ["readall"], "users": []}
        response = requests.put(
            f"https://{endpoint}/_plugins/_security/api/rolesmapping/readall",
            json=test_rolemapping,
            auth=master_user_auth,
        )
        assert response.status_code == 201

        # create a new user which is only mapped to the readall role
        test_user_auth = ("test_user", "J2j7Gun!30Abvy")
        test_user = {"password": test_user_auth[1], "backend_roles": ["readall"]}
        response = requests.put(
            f"https://{endpoint}/_plugins/_security/api/internalusers/{test_user_auth[0]}",
            json=test_user,
            auth=master_user_auth,
        )
        assert response.status_code == 201

        # ensure the user can only read but cannot write
        test_user_client = OpenSearch(hosts=endpoint, http_auth=test_user_auth)

        def _search():
            search_result = test_user_client.search(
                index=test_index_name, body={"query": {"match": {"test-key": "value"}}}
            )
            assert "hits" in search_result
            assert search_result["hits"]["hits"][0]["_source"] == test_document

        # it might take a bit for the document to be indexed
        retry(_search, sleep=0.5, retries=3)

        with pytest.raises(AuthorizationException):
            test_user_client.create(index="new-index2", id="new-index-id2", body={})

        with pytest.raises(AuthorizationException):
            test_user_client.index(index=test_index_name, body={"test-key1": "test-value1"})

        # add the user to the all_access role
        rolemappins_patch = [{"op": "add", "path": "/users/-", "value": "test_user"}]
        response = requests.patch(
            f"https://{endpoint}/_plugins/_security/api/rolesmapping/all_access",
            json=rolemappins_patch,
            auth=master_user_auth,
        )
        assert response.status_code == 200

        # ensure the user can now write and create a new index
        test_user_client.create(index="new-index2", id="new-index-id2", body={})
        test_user_client.index(index=test_index_name, body={"test-key1": "test-value1"})