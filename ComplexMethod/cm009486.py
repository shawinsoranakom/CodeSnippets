async def aadd_texts(
        self,
        texts: Iterable[str],
        metadatas: list[dict] | None = None,
        *,
        ids: list[str] | None = None,
        **kwargs: Any,
    ) -> list[str]:
        """Async run more texts through the embeddings and add to the `VectorStore`.

        Args:
            texts: Iterable of strings to add to the `VectorStore`.
            metadatas: Optional list of metadatas associated with the texts.
            ids: Optional list
            **kwargs: `VectorStore` specific parameters.

        Returns:
            List of IDs from adding the texts into the `VectorStore`.

        Raises:
            ValueError: If the number of metadatas does not match the number of texts.
            ValueError: If the number of IDs does not match the number of texts.
        """
        if ids is not None:
            # For backward compatibility
            kwargs["ids"] = ids
        if type(self).aadd_documents != VectorStore.aadd_documents:
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
            return await self.aadd_documents(docs, **kwargs)
        return await run_in_executor(None, self.add_texts, texts, metadatas, **kwargs)