def build_vector_store(self) -> Cassandra:
        try:
            import cassio
            from langchain_community.utilities.cassandra import SetupMode
        except ImportError as e:
            msg = "Could not import cassio integration package. Please install it with `pip install cassio`."
            raise ImportError(msg) from e

        from uuid import UUID

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

        # Convert DataFrame to Data if needed using parent's method
        self.ingest_data = self._prepare_ingest_data()

        documents = []
        for _input in self.ingest_data or []:
            if isinstance(_input, Data):
                documents.append(_input.to_lc_document())
            else:
                documents.append(_input)

        body_index_options = [("index_analyzer", "STANDARD")] if self.enable_body_search else None

        if self.setup_mode == "Off":
            setup_mode = SetupMode.OFF
        elif self.setup_mode == "Sync":
            setup_mode = SetupMode.SYNC
        else:
            setup_mode = SetupMode.ASYNC

        if documents:
            self.log(f"Adding {len(documents)} documents to the Vector Store.")
            table = Cassandra.from_documents(
                documents=documents,
                embedding=self.embedding,
                table_name=self.table_name,
                keyspace=self.keyspace,
                ttl_seconds=self.ttl_seconds or None,
                batch_size=self.batch_size,
                body_index_options=body_index_options,
            )
        else:
            self.log("No documents to add to the Vector Store.")
            table = Cassandra(
                embedding=self.embedding,
                table_name=self.table_name,
                keyspace=self.keyspace,
                ttl_seconds=self.ttl_seconds or None,
                body_index_options=body_index_options,
                setup_mode=setup_mode,
            )
        return table