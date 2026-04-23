def build_vector_store(self) -> MongoDBAtlasVectorSearch:
        try:
            from pymongo import MongoClient
        except ImportError as e:
            msg = "Please install pymongo to use MongoDB Atlas Vector Store"
            raise ImportError(msg) from e

        # Create temporary files for the client certificate
        if self.enable_mtls:
            client_cert_path = None
            try:
                client_cert = self.mongodb_atlas_client_cert.replace(" ", "\n")
                client_cert = client_cert.replace("-----BEGIN\nPRIVATE\nKEY-----", "-----BEGIN PRIVATE KEY-----")
                client_cert = client_cert.replace(
                    "-----END\nPRIVATE\nKEY-----\n-----BEGIN\nCERTIFICATE-----",
                    "-----END PRIVATE KEY-----\n-----BEGIN CERTIFICATE-----",
                )
                client_cert = client_cert.replace("-----END\nCERTIFICATE-----", "-----END CERTIFICATE-----")
                with tempfile.NamedTemporaryFile(delete=False) as client_cert_file:
                    client_cert_file.write(client_cert.encode("utf-8"))
                    client_cert_path = client_cert_file.name

            except Exception as e:
                msg = f"Failed to write certificate to temporary file: {e}"
                raise ValueError(msg) from e

        try:
            mongo_client: MongoClient = (
                MongoClient(
                    self.mongodb_atlas_cluster_uri,
                    tls=True,
                    tlsCertificateKeyFile=client_cert_path,
                    tlsCAFile=certifi.where(),
                )
                if self.enable_mtls
                else MongoClient(self.mongodb_atlas_cluster_uri)
            )

            collection = mongo_client[self.db_name][self.collection_name]

        except Exception as e:
            msg = f"Failed to connect to MongoDB Atlas: {e}"
            raise ValueError(msg) from e

        # Convert DataFrame to Data if needed using parent's method
        self.ingest_data = self._prepare_ingest_data()

        documents = []
        for _input in self.ingest_data or []:
            if isinstance(_input, Data):
                documents.append(_input.to_lc_document())
            else:
                documents.append(_input)

        if documents:
            self.__insert_mode(collection)

            return MongoDBAtlasVectorSearch.from_documents(
                documents=documents, embedding=self.embedding, collection=collection, index_name=self.index_name
            )
        return MongoDBAtlasVectorSearch(embedding=self.embedding, collection=collection, index_name=self.index_name)