def test_deleted_chunk_not_in_retrieval(self, HttpApiAuth, add_document):
        """
        Test that a deleted chunk is not returned by the retrieval API.

        Steps:
        1. Add a chunk with unique content
        2. Verify the chunk is retrievable
        3. Delete the chunk
        4. Verify the chunk is no longer retrievable
        """
        dataset_id, document_id = add_document

        # Add a chunk with unique content that we can search for
        unique_content = "UNIQUE_TEST_CONTENT_12520_REGRESSION"
        res = add_chunk(HttpApiAuth, dataset_id, document_id, {"content": unique_content})
        assert res["code"] == 0, f"Failed to add chunk: {res}"
        chunk_id = res["data"]["chunk"]["id"]

        # Wait for indexing to complete
        sleep(2)

        # Verify the chunk is retrievable
        payload = {"question": unique_content, "dataset_ids": [dataset_id]}
        res = retrieval_chunks(HttpApiAuth, payload)
        assert res["code"] == 0, f"Retrieval failed: {res}"
        chunk_ids_before = [c["id"] for c in res["data"]["chunks"]]
        assert chunk_id in chunk_ids_before, f"Chunk {chunk_id} should be retrievable before deletion"

        # Delete the chunk
        res = delete_chunks(HttpApiAuth, dataset_id, document_id, {"chunk_ids": [chunk_id]})
        assert res["code"] == 0, f"Failed to delete chunk: {res}"

        # Wait for deletion to propagate
        sleep(1)

        # Verify the chunk is no longer retrievable
        res = retrieval_chunks(HttpApiAuth, payload)
        assert res["code"] == 0, f"Retrieval failed after deletion: {res}"
        chunk_ids_after = [c["id"] for c in res["data"]["chunks"]]
        assert chunk_id not in chunk_ids_after, f"Chunk {chunk_id} should NOT be retrievable after deletion"