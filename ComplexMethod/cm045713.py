def format_inputs(
            metadatas: list[pw.Json] | None,
            metadata_filter: str | None,
            return_status: bool,
            is_parsed: list[bool] | None,
        ) -> list[pw.Json]:
            metadatas = metadatas if metadatas is not None else []
            is_parsed = is_parsed if is_parsed is not None else []
            assert metadatas is not None
            assert is_parsed is not None

            def remove_id(m):
                metadata_dict = m.as_dict()
                del metadata_dict["_file_id"]
                return pw.Json(metadata_dict)

            metadatas = [remove_id(m) for m in metadatas]
            if metadata_filter:
                metadatas = [
                    m
                    for m in metadatas
                    if jmespath.search(
                        metadata_filter, m.as_dict(), options=_knn_lsh._glob_options
                    )
                ]

            if return_status:
                metadatas = [
                    pw.Json(
                        {
                            "_indexing_status": (
                                IndexingStatus.INDEXED
                                if status
                                else IndexingStatus.INGESTED
                            ),
                            **m.as_dict(),
                        }
                    )
                    for (m, status) in zip(metadatas, is_parsed)
                ]

            return metadatas