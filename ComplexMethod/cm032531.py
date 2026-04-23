def test_deleted_chunks_batch_not_in_retrieval(self, HttpApiAuth, add_document):
        """
        Test that multiple deleted chunks are not returned by retrieval.
        """
        dataset_id, document_id = add_document

        # Add multiple chunks with unique content
        chunk_ids = []
        for i in range(3):
            unique_content = f"BATCH_DELETE_TEST_CHUNK_{i}_12520"
            res = add_chunk(HttpApiAuth, dataset_id, document_id, {"content": unique_content})
            assert res["code"] == 0, f"Failed to add chunk {i}: {res}"
            chunk_ids.append(res["data"]["chunk"]["id"])

        # Wait for indexing
        sleep(2)

        # Verify chunks are retrievable
        payload = {"question": "BATCH_DELETE_TEST_CHUNK", "dataset_ids": [dataset_id]}
        res = retrieval_chunks(HttpApiAuth, payload)
        assert res["code"] == 0
        retrieved_ids_before = [c["id"] for c in res["data"]["chunks"]]
        for cid in chunk_ids:
            assert cid in retrieved_ids_before, f"Chunk {cid} should be retrievable before deletion"

        # Delete all chunks
        res = delete_chunks(HttpApiAuth, dataset_id, document_id, {"chunk_ids": chunk_ids})
        assert res["code"] == 0, f"Failed to delete chunks: {res}"

        # Wait for deletion to propagate
        sleep(1)

        # Verify none of the chunks are retrievable
        res = retrieval_chunks(HttpApiAuth, payload)
        assert res["code"] == 0
        retrieved_ids_after = [c["id"] for c in res["data"]["chunks"]]
        for cid in chunk_ids:
            assert cid not in retrieved_ids_after, f"Chunk {cid} should NOT be retrievable after deletion"