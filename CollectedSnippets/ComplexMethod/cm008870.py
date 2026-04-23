async def test_delete_missing_docs(self, index: DocumentIndex) -> None:
        """Verify that we can delete docs that aren't there."""
        assert await index.aget(["1"]) == []  # Should be empty.

        delete_response = await index.adelete(["1"])
        if "num_deleted" in delete_response:
            assert delete_response["num_deleted"] == 0

        if "num_failed" in delete_response:
            # Deleting a missing an ID is **not** failure!!
            assert delete_response["num_failed"] == 0

        if "succeeded" in delete_response:
            # There was nothing to delete!
            assert delete_response["succeeded"] == []

        if "failed" in delete_response:
            # Nothing should have failed
            assert delete_response["failed"] == []