def _test_vs(fake_embeddings_model, **run_kwargs):
    docs = pw.debug.table_from_rows(
        schema=pw.schema_from_types(data=bytes, _metadata=dict),
        rows=[
            (
                "test".encode("utf-8"),
                {"path": "pathway/xpacks/llm/tests/test_vector_store.py"},
            )
        ],
    )

    vector_server = VectorStoreServer(
        docs,
        embedder=fake_embeddings_model,
    )

    info_queries = pw.debug.table_from_rows(
        schema=DebugStatsInputSchema,
        rows=[
            (None,),
        ],
    ).select()

    info_outputs = vector_server.statistics_query(info_queries)
    assert_table_equality(
        info_outputs.select(result=pw.unwrap(pw.this.result["file_count"].as_int())),
        pw.debug.table_from_markdown(
            """
            result
            1
            """
        ),
        **run_kwargs,
    )

    input_queries = pw.debug.table_from_rows(
        schema=VectorStoreServer.InputsQuerySchema,  # filter, pattern, return_status
        rows=[
            (None, "**/*.py", False),
        ],
    )

    input_outputs = vector_server.inputs_query(input_queries)

    @pw.udf
    def get_file_name(result_js) -> str:
        if len(result_js):
            return result_js[0]["path"].value.split("/")[-1].replace('"', "")
        else:
            return str(result_js)

    assert_table_equality(
        input_outputs.select(result=pw.unwrap(get_file_name(pw.this.result))),
        pw.debug.table_from_markdown(
            """
            result
            test_vector_store.py
            """
        ),
        **run_kwargs,
    )

    _, rows = pw.debug.table_to_dicts(input_outputs, **run_kwargs)
    (val,) = rows["result"].values()
    val = val[0]  # type: ignore

    assert isinstance(val, pw.Json)
    input_result = val.value
    assert isinstance(input_result, dict)

    assert "path" in input_result.keys()

    # parse_graph.G.clear()
    retrieve_queries = pw.debug.table_from_markdown(
        """
        query | k | metadata_filter | filepath_globpattern
        "Foo" | 1 |                 |
        """,
        schema=VectorStoreServer.RetrieveQuerySchema,
    )

    retrieve_outputs = vector_server.retrieve_query(retrieve_queries)
    _, rows = pw.debug.table_to_dicts(retrieve_outputs, **run_kwargs)
    (val,) = rows["result"].values()
    assert isinstance(val, pw.Json)
    (query_result,) = val.value  # type: ignore # extract the single match
    assert isinstance(query_result, dict)
    assert query_result["dist"] < 1.0e-6  # type: ignore # the dist is not 0 due to float normalization
    assert query_result["text"]