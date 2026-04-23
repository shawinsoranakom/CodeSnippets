def test_create_indices(self, opensearch_endpoint):
        indices = ["index1", "index2"]
        for index_name in indices:
            index_path = f"{opensearch_endpoint}/{index_name}"
            requests.put(index_path, headers=COMMON_HEADERS)
            endpoint = f"{opensearch_endpoint}/_cat/indices/{index_name}?format=json&pretty"
            req = requests.get(endpoint)
            assert req.status_code == 200
            req_result = json.loads(req.text)
            assert req_result[0]["health"] in ["green", "yellow"]
            assert req_result[0]["index"] in indices

        # create a knn index to make sure the knn plugin works
        index_path = f"{opensearch_endpoint}/knn"
        body = {
            "settings": {"index": {"knn": True}},
            "mappings": {
                "properties": {
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": 2,
                    }
                }
            },
        }
        put = requests.put(index_path, headers=COMMON_HEADERS, json=body)
        assert put.status_code == 200
        get = requests.get(f"{opensearch_endpoint}/_cat/indices/knn?format=json&pretty")
        assert get.status_code == 200

        # add a document
        document_path = f"{opensearch_endpoint}/knn/_doc/test_document"
        body = {"embedding": [1, 2]}
        put = requests.put(document_path, headers=COMMON_HEADERS, json=body)
        assert put.status_code == 201

        get = requests.get(document_path)
        assert get.status_code == 200