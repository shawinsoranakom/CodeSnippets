def build_vector_store(self) -> Qdrant:
        qdrant_kwargs = {
            "collection_name": self.collection_name,
            "content_payload_key": self.content_payload_key,
            "metadata_payload_key": self.metadata_payload_key,
        }

        server_kwargs = {
            "host": self.host or None,
            "port": int(self.port),  # Ensure port is an integer
            "grpc_port": int(self.grpc_port),  # Ensure grpc_port is an integer
            "api_key": self.api_key,
            "prefix": self.prefix,
            # Ensure timeout is an integer
            "timeout": int(self.timeout) if self.timeout else None,
            "path": self.path or None,
            "url": self.url or None,
        }

        server_kwargs = {k: v for k, v in server_kwargs.items() if v is not None}

        # Convert DataFrame to Data if needed using parent's method
        self.ingest_data = self._prepare_ingest_data()

        documents = []
        for _input in self.ingest_data or []:
            if isinstance(_input, Data):
                documents.append(_input.to_lc_document())
            else:
                documents.append(_input)

        if not isinstance(self.embedding, Embeddings):
            msg = "Invalid embedding object"
            raise TypeError(msg)

        if documents:
            qdrant = Qdrant.from_documents(documents, embedding=self.embedding, **qdrant_kwargs, **server_kwargs)
        else:
            from qdrant_client import QdrantClient

            client = QdrantClient(**server_kwargs)
            qdrant = Qdrant(embeddings=self.embedding, client=client, **qdrant_kwargs)

        return qdrant