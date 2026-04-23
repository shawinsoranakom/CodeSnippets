def build_vector_store(self) -> Weaviate:
        if self.api_key:
            auth_config = weaviate.AuthApiKey(api_key=self.api_key)
            client = weaviate.Client(url=self.url, auth_client_secret=auth_config)
        else:
            client = weaviate.Client(url=self.url)

        if self.index_name != self.index_name.capitalize():
            msg = f"Weaviate requires the index name to be capitalized. Use: {self.index_name.capitalize()}"
            raise ValueError(msg)

        # Convert DataFrame to Data if needed using parent's method
        self.ingest_data = self._prepare_ingest_data()

        documents = []
        for _input in self.ingest_data or []:
            if isinstance(_input, Data):
                documents.append(_input.to_lc_document())
            else:
                documents.append(_input)

        if documents and self.embedding:
            return Weaviate.from_documents(
                client=client,
                index_name=self.index_name,
                documents=documents,
                embedding=self.embedding,
                by_text=self.search_by_text,
            )

        return Weaviate(
            client=client,
            index_name=self.index_name,
            text_key=self.text_key,
            embedding=self.embedding,
            by_text=self.search_by_text,
        )