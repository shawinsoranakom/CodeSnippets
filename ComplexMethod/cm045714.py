def format_inputs(
            metadatas: list[pw.Json] | None,
            metadata_filter: str | None,
        ) -> list[pw.Json]:
            metadatas = metadatas if metadatas is not None else []
            if metadata_filter:
                metadatas = [
                    m
                    for m in metadatas
                    if jmespath.search(
                        metadata_filter, m.value, options=_knn_lsh._glob_options
                    )
                ]

            metadata_list: list[dict] = [m.as_dict() for m in metadatas]

            for metadata in metadata_list:
                for metadata_key in self.excluded_response_metadata:
                    metadata.pop(metadata_key, None)

            return [pw.Json(m) for m in metadata_list]