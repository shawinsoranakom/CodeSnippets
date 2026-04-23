def test_parser_config(
        self,
        HttpApiAuth,
        add_documents,
        chunk_method,
        parser_config,
        expected_code,
        expected_message,
    ):
        dataset_id, document_ids = add_documents
        res = update_document(
            HttpApiAuth,
            dataset_id,
            document_ids[0],
            {"chunk_method": chunk_method, "parser_config": parser_config},
        )
        assert res["code"] == expected_code
        if expected_code == 0:
            res = list_documents(HttpApiAuth, dataset_id, {"id": document_ids[0]})

            doc_of_id = res["data"]["docs"][0]
            if parser_config == {}:
                assert doc_of_id["parser_config"] == DEFAULT_PARSER_CONFIG
            else:
                for k, v in parser_config.items():
                    assert doc_of_id["parser_config"][k] == v
        if expected_code != 0 or expected_message:
            assert res["message"] == expected_message