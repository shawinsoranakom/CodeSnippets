def add_texts(
        self,
        texts: Iterable[str],
        metadatas: list[dict] | None = None,
        ids: list[str] | None = None,
        **kwargs: Any,
    ) -> list[str]:
        if not isinstance(texts, list):
            texts = list(texts)
        ids_iter = iter(ids or [])

        ids_ = []

        metadatas_ = metadatas or [{} for _ in texts]

        for text, metadata in zip(texts, metadatas_ or [], strict=False):
            next_id = next(ids_iter, None)
            id_ = next_id or str(uuid.uuid4())
            self.store[id_] = Document(page_content=text, metadata=metadata, id=id_)
            ids_.append(id_)
        return ids_