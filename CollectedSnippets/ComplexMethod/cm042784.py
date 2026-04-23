def test_summarize_with_metadata_and_document_context(test_client: TestClient) -> None:
    docs = []

    # Ingest a first document
    document_1_content = "Content of document 1"
    ingest_response = test_client.post(
        "/v1/ingest/text",
        json={
            "file_name": "file_name_1",
            "text": document_1_content,
        },
    )
    assert ingest_response.status_code == 200
    ingested_docs = ingest_response.json()["data"]
    assert len(ingested_docs) == 1
    docs += ingested_docs

    # Ingest a second document
    document_2_content = "Text of document 2"
    ingest_response = test_client.post(
        "/v1/ingest/text",
        json={
            "file_name": "file_name_2",
            "text": document_2_content,
        },
    )
    assert ingest_response.status_code == 200
    ingested_docs = ingest_response.json()["data"]
    assert len(ingested_docs) == 1
    docs += ingested_docs

    # Completions with the first document's id and the second document's metadata
    body = SummarizeBody(
        use_context=True,
        context_filter={"docs_ids": [doc["doc_id"] for doc in docs]},
        stream=False,
    )
    response = test_client.post("/v1/summarize", json=body.model_dump())

    completion: SummarizeResponse = SummarizeResponse.model_validate(response.json())
    assert response.status_code == 200
    # Assert both documents are part of the used sources
    # We can check the content of the completion, because mock LLM used in tests
    # always echoes the prompt. In the case of summary, the input context is passed.
    assert completion.summary.find(document_1_content) != -1
    assert completion.summary.find(document_2_content) != -1