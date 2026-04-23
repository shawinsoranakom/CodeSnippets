def add_documents(
        self,
        documents: list[Document],
        ids: list[str] | None = None,
        **kwargs: Any,
    ) -> list[str]:
        texts = [doc.page_content for doc in documents]
        vectors = self.embedding.embed_documents(texts)

        if ids and len(ids) != len(texts):
            msg = (
                f"ids must be the same length as texts. "
                f"Got {len(ids)} ids and {len(texts)} texts."
            )
            raise ValueError(msg)

        id_iterator: Iterator[str | None] = (
            iter(ids) if ids else iter(doc.id for doc in documents)
        )

        ids_ = []

        for doc, vector in zip(documents, vectors, strict=False):
            doc_id = next(id_iterator)
            doc_id_ = doc_id or str(uuid.uuid4())
            ids_.append(doc_id_)
            self.store[doc_id_] = {
                "id": doc_id_,
                "vector": vector,
                "text": doc.page_content,
                "metadata": doc.metadata,
            }

        return ids_