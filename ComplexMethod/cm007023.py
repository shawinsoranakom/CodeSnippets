def search_documents(self, vector_store=None) -> list[Data]:
        if not vector_store:
            vector_store = self.build_vector_store()

        self.log("Searching for documents in AstraDBGraphVectorStore.")
        self.log(f"Search query: {self.search_query}")
        self.log(f"Search type: {self.search_type}")
        self.log(f"Number of results: {self.number_of_results}")

        if self.search_query and isinstance(self.search_query, str) and self.search_query.strip():
            try:
                search_type = self._map_search_type()
                search_args = self._build_search_args()

                docs = vector_store.search(query=self.search_query, search_type=search_type, **search_args)

                # Drop links from the metadata. At this point the links don't add any value for building the
                # context and haven't been restored to json which causes the conversion to fail.
                self.log("Removing links from metadata.")
                for doc in docs:
                    if "links" in doc.metadata:
                        doc.metadata.pop("links")

            except Exception as e:
                msg = f"Error performing search in AstraDBGraphVectorStore: {e}"
                raise ValueError(msg) from e

            self.log(f"Retrieved documents: {len(docs)}")

            data = docs_to_data(docs)

            self.log(f"Converted documents to data: {len(data)}")

            self.status = data
            return data
        self.log("No search input provided. Skipping search.")
        return []