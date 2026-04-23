def build_vector_store(self) -> CassandraGraphVectorStore:
        try:
            import cassio
            from langchain_community.utilities.cassandra import SetupMode
        except ImportError as e:
            msg = "Could not import cassio integration package. Please install it with `pip install cassio`."
            raise ImportError(msg) from e

        database_ref = self.database_ref

        try:
            UUID(self.database_ref)
            is_astra = True
        except ValueError:
            is_astra = False
            if "," in self.database_ref:
                # use a copy because we can't change the type of the parameter
                database_ref = self.database_ref.split(",")

        if is_astra:
            cassio.init(
                database_id=database_ref,
                token=self.token,
                cluster_kwargs=self.cluster_kwargs,
            )
        else:
            cassio.init(
                contact_points=database_ref,
                username=self.username,
                password=self.token,
                cluster_kwargs=self.cluster_kwargs,
            )

        self.ingest_data = self._prepare_ingest_data()

        documents = []

        for _input in self.ingest_data or []:
            if isinstance(_input, Data):
                documents.append(_input.to_lc_document())
            else:
                documents.append(_input)

        setup_mode = SetupMode.OFF if self.setup_mode == "Off" else SetupMode.SYNC

        if documents:
            self.log(f"Adding {len(documents)} documents to the Vector Store.")
            store = CassandraGraphVectorStore.from_documents(
                documents=documents,
                embedding=self.embedding,
                node_table=self.table_name,
                keyspace=self.keyspace,
            )
        else:
            self.log("No documents to add to the Vector Store.")
            store = CassandraGraphVectorStore(
                embedding=self.embedding,
                node_table=self.table_name,
                keyspace=self.keyspace,
                setup_mode=setup_mode,
            )
        return store