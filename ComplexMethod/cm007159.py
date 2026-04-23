def build_vector_store(self) -> ElasticsearchStore:
        """Builds the Elasticsearch Vector Store object."""
        if self.cloud_id and self.elasticsearch_url:
            msg = (
                "Both 'cloud_id' and 'elasticsearch_url' provided. "
                "Please use only one based on your deployment (Cloud or Local)."
            )
            raise ValueError(msg)

        es_params = {
            "index_name": self.index_name,
            "embedding": self.embedding,
            "es_user": self.username or None,
            "es_password": self.password or None,
        }

        if self.cloud_id:
            es_params["es_cloud_id"] = self.cloud_id
        else:
            es_params["es_url"] = self.elasticsearch_url

        if self.api_key:
            es_params["api_key"] = self.api_key

        # Check if we need to verify SSL certificates
        if self.verify_certs is False:
            # Build client parameters for Elasticsearch constructor
            client_params: dict[str, Any] = {}
            client_params["verify_certs"] = False

            if self.cloud_id:
                client_params["cloud_id"] = self.cloud_id
            else:
                client_params["hosts"] = [self.elasticsearch_url]

            if self.api_key:
                client_params["api_key"] = self.api_key
            elif self.username and self.password:
                client_params["basic_auth"] = (self.username, self.password)

            es_client = Elasticsearch(**client_params)
            es_params["es_connection"] = es_client

        elasticsearch = ElasticsearchStore(**es_params)

        # If documents are provided, add them to the store
        if self.ingest_data:
            documents = self._prepare_documents()
            if documents:
                elasticsearch.add_documents(documents)

        return elasticsearch