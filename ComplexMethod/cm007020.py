def run_model(self, **args) -> Data | list[Data]:
        """Run the query to get the data from the Astra DB collection."""
        sort = {}

        # Build filters using the new method
        filters = self.build_filter(args, self.tools_params_v2)

        # Build the vector search on
        if self.use_search_query and args["search_query"] is not None and args["search_query"] != "":
            if self.use_vectorize:
                sort["$vectorize"] = args["search_query"]
            else:
                if self.embedding is None:
                    msg = "Embedding model is not set. Please set the embedding model or use Astra DB Vectorize."
                    logger.error(msg)
                    raise ValueError(msg)
                embedding_query = self.embedding.embed_query(args["search_query"])
                sort["$vector"] = embedding_query
            del args["search_query"]

        find_options = {
            "filter": filters,
            "limit": self.number_of_results,
            "sort": sort,
        }

        projection = self.projection_args(self.projection_attributes)
        if projection and len(projection) > 0:
            find_options["projection"] = projection

        try:
            database = self.get_database_object(api_endpoint=self.get_api_endpoint())
            collection = database.get_collection(
                name=self.collection_name,
                keyspace=self.get_keyspace(),
            )
            results = collection.find(**find_options)
        except Exception as e:
            msg = f"Error on Astra DB Tool {self.tool_name} request: {e}"
            logger.error(msg)
            raise ValueError(msg) from e

        logger.info(f"Tool {self.tool_name} executed`")

        data: list[Data] = [Data(data=doc) for doc in results]
        self.status = data
        return data