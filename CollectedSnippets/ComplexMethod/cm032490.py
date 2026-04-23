def test_chunk_method(self, add_documents, chunk_method, expected_message):
        dataset, documents = add_documents
        document = documents[0]

        if expected_message:
            if chunk_method == "":
                # Check if empty string raises an exception or not
                try:
                    document.update({"chunk_method": chunk_method})
                    # If no exception is raised, skip this test
                    pytest.skip("Empty chunk_method doesn't raise an exception as expected")
                except Exception as e:
                    assert expected_message in str(e), str(e)
            elif chunk_method == "other_chunk_method":
                with pytest.raises(Exception) as exception_info:
                    document.update({"chunk_method": chunk_method})
                assert expected_message in str(exception_info.value), str(exception_info.value)
            else:
                with pytest.raises(Exception) as exception_info:
                    document.update({"chunk_method": chunk_method})
                assert expected_message in str(exception_info.value), str(exception_info.value)
        else:
            document.update({"chunk_method": chunk_method})
            docs = dataset.list_documents()
            updated_doc = [doc for doc in docs if doc.id == document.id][0]
            assert updated_doc.chunk_method == chunk_method, str(updated_doc)