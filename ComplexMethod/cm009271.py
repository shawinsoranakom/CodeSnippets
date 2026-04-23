def add_images(
        self,
        uris: list[str],
        metadatas: list[dict] | None = None,
        ids: list[str] | None = None,
    ) -> list[str]:
        """Run more images through the embeddings and add to the `VectorStore`.

        Args:
            uris: File path to the image.
            metadatas: Optional list of metadatas.
                    When querying, you can filter on this metadata.
            ids: Optional list of IDs. (Items without IDs will be assigned UUIDs)

        Returns:
            List of IDs of the added images.

        Raises:
            ValueError: When metadata is incorrect.
        """
        # Map from uris to b64 encoded strings
        b64_texts = [self.encode_image(uri=uri) for uri in uris]
        # Populate IDs
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in uris]
        else:
            ids = [id_ if id_ is not None else str(uuid.uuid4()) for id_ in ids]
        embeddings = None
        # Set embeddings
        if self._embedding_function is not None and hasattr(
            self._embedding_function,
            "embed_image",
        ):
            embeddings = self._embedding_function.embed_image(uris=uris)
        if metadatas:
            # fill metadatas with empty dicts if somebody
            # did not specify metadata for all images
            length_diff = len(uris) - len(metadatas)
            if length_diff:
                metadatas = metadatas + [{}] * length_diff
            empty_ids = []
            non_empty_ids = []
            for idx, m in enumerate(metadatas):
                if m:
                    non_empty_ids.append(idx)
                else:
                    empty_ids.append(idx)
            if non_empty_ids:
                metadatas = [metadatas[idx] for idx in non_empty_ids]
                images_with_metadatas = [b64_texts[idx] for idx in non_empty_ids]
                embeddings_with_metadatas = (
                    [embeddings[idx] for idx in non_empty_ids] if embeddings else None
                )
                ids_with_metadata = [ids[idx] for idx in non_empty_ids]
                try:
                    self._collection.upsert(
                        metadatas=metadatas,  # type: ignore[arg-type]
                        embeddings=embeddings_with_metadatas,  # type: ignore[arg-type]
                        documents=images_with_metadatas,
                        ids=ids_with_metadata,
                    )
                except ValueError as e:
                    if "Expected metadata value to be" in str(e):
                        msg = (
                            "Try filtering complex metadata using "
                            "langchain_community.vectorstores.utils.filter_complex_metadata."
                        )
                        raise ValueError(e.args[0] + "\n\n" + msg) from e
                    raise e
            if empty_ids:
                images_without_metadatas = [b64_texts[j] for j in empty_ids]
                embeddings_without_metadatas = (
                    [embeddings[j] for j in empty_ids] if embeddings else None
                )
                ids_without_metadatas = [ids[j] for j in empty_ids]
                self._collection.upsert(
                    embeddings=embeddings_without_metadatas,
                    documents=images_without_metadatas,
                    ids=ids_without_metadatas,
                )
        else:
            self._collection.upsert(
                embeddings=embeddings,
                documents=b64_texts,
                ids=ids,
            )
        return ids