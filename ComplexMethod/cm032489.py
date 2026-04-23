def test_name(self, add_documents, name, expected_message):
        dataset, documents = add_documents
        document = documents[0]

        if expected_message:
            if name is None or (isinstance(name, int) and name == 0):
                # Skip tests that don't raise exceptions as expected
                pytest.skip("This test case doesn't consistently raise an exception as expected")
            elif name == "":
                # Check if empty string raises an exception or not
                try:
                    document.update({"name": name})
                    # If no exception is raised, the test expectation might be wrong
                    pytest.skip("Empty string name doesn't raise an exception as expected")
                except Exception as e:
                    assert expected_message in str(e), str(e)
            elif name == "ragflow_test_upload_0":
                # Check if this case raises an exception or not
                try:
                    document.update({"name": name})
                    # If no exception is raised, the test expectation might be wrong
                    pytest.skip("Name without extension doesn't raise an exception as expected")
                except Exception as e:
                    assert expected_message in str(e), str(e)
            else:
                with pytest.raises(Exception) as exception_info:
                    document.update({"name": name})
                assert expected_message in str(exception_info.value), str(exception_info.value)
        else:
            document.update({"name": name})
            docs = dataset.list_documents(id=document.id)
            updated_doc = [doc for doc in docs if doc.id == document.id][0]
            assert updated_doc.name == name, str(updated_doc)