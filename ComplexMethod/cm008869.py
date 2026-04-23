def test_delete_semantics(self, index: DocumentIndex) -> None:
        """Test deletion of content has appropriate semantics."""
        # Let's index a document first.
        foo_uuid = str(uuid.UUID(int=7))
        upsert_response = index.upsert(
            [Document(id=foo_uuid, page_content="foo", metadata={})]
        )
        assert upsert_response == {"succeeded": [foo_uuid], "failed": []}

        delete_response = index.delete(["missing_id", foo_uuid])

        if "num_deleted" in delete_response:
            assert delete_response["num_deleted"] == 1

        if "num_failed" in delete_response:
            # Deleting a missing an ID is **not** failure!!
            assert delete_response["num_failed"] == 0

        if "succeeded" in delete_response:
            # There was nothing to delete!
            assert delete_response["succeeded"] == [foo_uuid]

        if "failed" in delete_response:
            # Nothing should have failed
            assert delete_response["failed"] == []