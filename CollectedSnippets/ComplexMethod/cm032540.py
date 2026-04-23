def test_concurrent_add_chunk(self, HttpApiAuth, add_document):
        count = 50
        dataset_id, document_id = add_document
        res = list_chunks(HttpApiAuth, dataset_id, document_id)
        if res["code"] != 0:
            assert False, res
        chunks_count = res["data"]["doc"]["chunk_count"]

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(
                    add_chunk,
                    HttpApiAuth,
                    dataset_id,
                    document_id,
                    {"content": f"chunk test {i}"},
                )
                for i in range(count)
            ]
        responses = list(as_completed(futures))
        assert len(responses) == count, responses
        assert all(future.result()["code"] == 0 for future in futures)
        res = list_chunks(HttpApiAuth, dataset_id, document_id)
        if res["code"] != 0:
            assert False, res
        assert res["data"]["doc"]["chunk_count"] == chunks_count + count