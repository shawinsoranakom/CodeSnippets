def test_parser_config(self, client, add_documents, chunk_method, parser_config, expected_message):
        dataset, documents = add_documents
        document = documents[0]
        from operator import attrgetter

        update_data = {"chunk_method": chunk_method, "parser_config": parser_config}

        if expected_message:
            with pytest.raises(Exception) as exception_info:
                document.update(update_data)
            assert expected_message in str(exception_info.value), str(exception_info.value)
        else:
            document.update(update_data)
            docs = dataset.list_documents(id=document.id)
            updated_doc = [doc for doc in docs if doc.id == document.id][0]
            if parser_config:
                for k, v in parser_config.items():
                    if isinstance(v, dict):
                        for kk, vv in v.items():
                            assert attrgetter(f"{k}.{kk}")(updated_doc.parser_config) == vv, str(updated_doc)
                    else:
                        assert attrgetter(k)(updated_doc.parser_config) == v, str(updated_doc)
            else:
                expected_config = DataSet.ParserConfig(
                    client,
                    DEFAULT_PARSER_CONFIG,
                )
                assert str(updated_doc.parser_config) == str(expected_config), str(updated_doc)