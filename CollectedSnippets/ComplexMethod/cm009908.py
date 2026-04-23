def _split_docs_for_adding(
        self,
        documents: list[Document],
        ids: list[str] | None = None,
        *,
        add_to_docstore: bool = True,
    ) -> tuple[list[Document], list[tuple[str, Document]]]:
        if self.parent_splitter is not None:
            documents = self.parent_splitter.split_documents(documents)
        if ids is None:
            doc_ids = [str(uuid.uuid4()) for _ in documents]
            if not add_to_docstore:
                msg = "If IDs are not passed in, `add_to_docstore` MUST be True"
                raise ValueError(msg)
        else:
            if len(documents) != len(ids):
                msg = (
                    "Got uneven list of documents and ids. "
                    "If `ids` is provided, should be same length as `documents`."
                )
                raise ValueError(msg)
            doc_ids = ids

        docs = []
        full_docs = []
        for i, doc in enumerate(documents):
            _id = doc_ids[i]
            sub_docs = self.child_splitter.split_documents([doc])
            if self.child_metadata_fields is not None:
                for _doc in sub_docs:
                    _doc.metadata = {
                        k: _doc.metadata[k] for k in self.child_metadata_fields
                    }
            for _doc in sub_docs:
                _doc.metadata[self.id_key] = _id
            docs.extend(sub_docs)
            full_docs.append((_id, doc))

        return docs, full_docs