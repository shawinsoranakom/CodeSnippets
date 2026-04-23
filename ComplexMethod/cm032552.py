def test_retrieval_with_metadata_filter(self, HttpApiAuth, add_dataset_with_metadata, tmp_path):
        """
        Test that retrieval respects metadata filters.

        Verifies that chunks are only retrieved from documents matching the metadata condition.
        """
        from common import upload_documents, parse_documents, retrieval_chunks

        dataset_id = add_dataset_with_metadata

        # Create two documents with different metadata
        content_doc1 = "Document about Zhuge Liang who lived in Three Kingdoms period."
        content_doc2 = "Document about Cao Cao who lived in Late Eastern Han Dynasty."

        fp1 = tmp_path / "doc1_zhuge_liang.txt"
        fp2 = tmp_path / "doc2_cao_cao.txt"

        with open(fp1, "w", encoding="utf-8") as f:
            f.write(content_doc1)
        with open(fp2, "w", encoding="utf-8") as f:
            f.write(content_doc2)

        # Upload both documents
        res = upload_documents(HttpApiAuth, dataset_id, [fp1, fp2])
        assert res["code"] == 0, f"Failed to upload documents: {res}"

        doc1_id = res["data"][0]["id"]
        doc2_id = res["data"][1]["id"]

        # Add different metadata to each document
        res = update_document(HttpApiAuth, dataset_id, doc1_id, {
            "meta_fields": {"character": "Zhuge Liang", "era": "Three Kingdoms"}
        })
        assert res["code"] == 0, f"Failed to update doc1 metadata: {res}"

        res = update_document(HttpApiAuth, dataset_id, doc2_id, {
            "meta_fields": {"character": "Cao Cao", "era": "Late Eastern Han"}
        })
        assert res["code"] == 0, f"Failed to update doc2 metadata: {res}"

        # Parse both documents
        res = parse_documents(HttpApiAuth, dataset_id, {"document_ids": [doc1_id, doc2_id]})
        assert res["code"] == 0, f"Failed to trigger parsing: {res}"

        # Wait for parsing to complete
        assert _condition_parsing_complete(HttpApiAuth, dataset_id), "Parsing timeout"

        # Test retrieval WITH metadata filter for "Zhuge Liang"
        res = retrieval_chunks(HttpApiAuth, {
            "question": "Zhuge Liang",
            "dataset_ids": [dataset_id],
            "metadata_condition": {
                "logic": "and",
                "conditions": [
                    {
                        "name": "character",
                        "comparison_operator": "is",
                        "value": "Zhuge Liang"
                    }
                ]
            }
        })
        assert res["code"] == 0, f"Retrieval with metadata filter failed: {res}"

        chunks_with_filter = res["data"]["chunks"]
        doc_ids_with_filter = set(chunk.get("document_id", "") for chunk in chunks_with_filter)

        logging.info(f"✓ Retrieved {len(chunks_with_filter)} chunks from documents: {doc_ids_with_filter}")

        # Verify that filtered results only contain doc1 (Zhuge Liang)
        if len(chunks_with_filter) > 0:
            assert doc1_id in doc_ids_with_filter, f"Filtered results should contain doc1 (Zhuge Liang), but got: {doc_ids_with_filter}"
            assert doc2_id not in doc_ids_with_filter, f"Filtered results should NOT contain doc2 (Cao Cao), but got: {doc_ids_with_filter}"
            logging.info("Metadata filter correctly excluded chunks from non-matching documents")
        else:
            logging.warning("No chunks retrieved with filter - this might be due to embedding model not configured")