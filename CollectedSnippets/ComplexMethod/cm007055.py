def _add_documents_to_vector_store(self, vector_store: "Chroma") -> None:
        """Adds documents to the Vector Store."""
        ingest_data: list | Data | DataFrame = self.ingest_data
        if not ingest_data:
            self.status = ""
            return

        # Convert DataFrame to Data if needed using parent's method
        ingest_data = self._prepare_ingest_data()

        stored_documents_without_id = []
        if self.allow_duplicates:
            stored_data = []
        else:
            limit = int(self.limit) if self.limit is not None and str(self.limit).strip() else None
            stored_data = chroma_collection_to_data(vector_store.get(limit=limit))
            for value in deepcopy(stored_data):
                del value.id
                stored_documents_without_id.append(value)

        documents = []
        for _input in ingest_data or []:
            if isinstance(_input, Data):
                if _input not in stored_documents_without_id:
                    documents.append(_input.to_lc_document())
            else:
                msg = "Vector Store Inputs must be Data objects."
                raise TypeError(msg)

        if documents and self.embedding is not None:
            self.log(f"Adding {len(documents)} documents to the Vector Store.")
            # Filter complex metadata to prevent ChromaDB errors
            try:
                from langchain_community.vectorstores.utils import filter_complex_metadata

                filtered_documents = filter_complex_metadata(documents)
                vector_store.add_documents(filtered_documents)
            except ImportError:
                self.log("Warning: Could not import filter_complex_metadata. Adding documents without filtering.")
                vector_store.add_documents(documents)
        else:
            self.log("No documents to add to the Vector Store.")