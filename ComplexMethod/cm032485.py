def test_id(self, add_chunks, chunk_id, expected_page_size, expected_message):
        _, document, chunks = add_chunks
        if callable(chunk_id) and get_doc_engine(document.rag) == "infinity":
            pytest.skip("issues/6499")
        chunk_ids = [chunk.id for chunk in chunks]
        if callable(chunk_id):
            params = {"id": chunk_id(chunk_ids)}
        else:
            params = {"id": chunk_id}

        if expected_message:
            with pytest.raises(Exception) as exception_info:
                document.list_chunks(**params)
            assert expected_message in str(exception_info.value), str(exception_info.value)
        else:
            chunks = document.list_chunks(**params)
            if params["id"] in [None, ""]:
                assert len(chunks) == expected_page_size, str(chunks)
            else:
                assert chunks[0].id == params["id"], str(chunks)