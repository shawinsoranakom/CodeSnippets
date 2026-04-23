def build_vector_store(self) -> VectorStore:
        """Build and return a Pinecone vector store instance."""
        try:
            from langchain_pinecone import PineconeVectorStore
        except ImportError as e:
            msg = "langchain-pinecone is not installed. Please install it with `pip install langchain-pinecone`."
            raise ValueError(msg) from e

        try:
            from langchain_pinecone._utilities import DistanceStrategy

            # Wrap the embedding model to ensure float32 output
            wrapped_embeddings = Float32Embeddings(self.embedding)

            # Convert distance strategy
            distance_strategy = self.distance_strategy.replace(" ", "_").upper()
            distance_strategy = DistanceStrategy[distance_strategy]

            # Initialize Pinecone instance with wrapped embeddings
            pinecone = PineconeVectorStore(
                index_name=self.index_name,
                embedding=wrapped_embeddings,  # Use wrapped embeddings
                text_key=self.text_key,
                namespace=self.namespace,
                distance_strategy=distance_strategy,
                pinecone_api_key=self.pinecone_api_key,
            )
        except Exception as e:
            error_msg = "Error building Pinecone vector store"
            raise ValueError(error_msg) from e
        else:
            self.ingest_data = self._prepare_ingest_data()

            # Process documents if any
            documents = []
            if self.ingest_data:
                # Convert DataFrame to Data if needed using parent's method

                for doc in self.ingest_data:
                    if isinstance(doc, Data):
                        documents.append(doc.to_lc_document())
                    else:
                        documents.append(doc)

                if documents:
                    pinecone.add_documents(documents)

            return pinecone