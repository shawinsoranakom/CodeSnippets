def add_texts(
        self,
        texts: Iterable[str],
        metadatas: list[dict] | None = None,
        *,
        ids: list[str] | None = None,
        **kwargs: Any,
    ) -> list[str]:
        """Run more texts through the embeddings and add to the `VectorStore`.

        Args:
            texts: Iterable of strings to add to the `VectorStore`.
            metadatas: Optional list of metadatas associated with the texts.
            ids: Optional list of IDs associated with the texts.
            **kwargs: `VectorStore` specific parameters.

                One of the kwargs should be `ids` which is a list of ids
                associated with the texts.

        Returns:
            List of IDs from adding the texts into the `VectorStore`.

        Raises:
            ValueError: If the number of metadatas does not match the number of texts.
            ValueError: If the number of IDs does not match the number of texts.
        """
        if type(self).add_documents != VectorStore.add_documents:
            # This condition is triggered if the subclass has provided
            # an implementation of the upsert method.
            # The existing add_texts
            texts_: Sequence[str] = (
                texts if isinstance(texts, (list, tuple)) else list(texts)
            )
            if metadatas and len(metadatas) != len(texts_):
                msg = (
                    "The number of metadatas must match the number of texts."
                    f"Got {len(metadatas)} metadatas and {len(texts_)} texts."
                )
                raise ValueError(msg)
            metadatas_ = iter(metadatas) if metadatas else cycle([{}])
            ids_: Iterator[str | None] = iter(ids) if ids else cycle([None])
            docs = [
                Document(id=id_, page_content=text, metadata=metadata_)
                for text, metadata_, id_ in zip(texts, metadatas_, ids_, strict=False)
            ]
            if ids is not None:
                # For backward compatibility
                kwargs["ids"] = ids

            return self.add_documents(docs, **kwargs)
        msg = f"`add_texts` has not been implemented for {self.__class__.__name__} "
        raise NotImplementedError(msg)