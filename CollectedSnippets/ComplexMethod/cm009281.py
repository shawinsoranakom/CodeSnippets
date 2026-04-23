async def aconstruct_instance(
        cls: type[Qdrant],
        texts: list[str],
        embedding: Embeddings,
        location: str | None = None,
        url: str | None = None,
        port: int | None = 6333,
        grpc_port: int = 6334,
        prefer_grpc: bool = False,  # noqa: FBT001, FBT002
        https: bool | None = None,  # noqa: FBT001
        api_key: str | None = None,
        prefix: str | None = None,
        timeout: int | None = None,
        host: str | None = None,
        path: str | None = None,
        collection_name: str | None = None,
        distance_func: str = "Cosine",
        content_payload_key: str = CONTENT_KEY,
        metadata_payload_key: str = METADATA_KEY,
        vector_name: str | None = VECTOR_NAME,
        shard_number: int | None = None,
        replication_factor: int | None = None,
        write_consistency_factor: int | None = None,
        on_disk_payload: bool | None = None,  # noqa: FBT001
        hnsw_config: models.HnswConfigDiff | None = None,
        optimizers_config: models.OptimizersConfigDiff | None = None,
        wal_config: models.WalConfigDiff | None = None,
        quantization_config: models.QuantizationConfig | None = None,
        init_from: models.InitFrom | None = None,
        on_disk: bool | None = None,  # noqa: FBT001
        force_recreate: bool = False,  # noqa: FBT001, FBT002
        **kwargs: Any,
    ) -> Qdrant:
        # Just do a single quick embedding to get vector size
        partial_embeddings = await embedding.aembed_documents(texts[:1])
        vector_size = len(partial_embeddings[0])
        collection_name = collection_name or uuid.uuid4().hex
        distance_func = distance_func.upper()
        client, async_client = cls._generate_clients(
            location=location,
            url=url,
            port=port,
            grpc_port=grpc_port,
            prefer_grpc=prefer_grpc,
            https=https,
            api_key=api_key,
            prefix=prefix,
            timeout=timeout,
            host=host,
            path=path,
            **kwargs,
        )

        collection_exists = client.collection_exists(collection_name)

        if collection_exists and force_recreate:
            client.delete_collection(collection_name)
            collection_exists = False

        if collection_exists:
            # Get the vector configuration of the existing collection and vector, if it
            # was specified. If the old configuration does not match the current one,
            # an exception is raised.
            collection_info = client.get_collection(collection_name=collection_name)
            current_vector_config = collection_info.config.params.vectors
            if isinstance(current_vector_config, dict) and vector_name is not None:
                if vector_name not in current_vector_config:
                    msg = (
                        f"Existing Qdrant collection {collection_name} does not "
                        f"contain vector named {vector_name}. Did you mean one of the "
                        f"existing vectors: {', '.join(current_vector_config.keys())}? "
                        f"If you want to recreate the collection, set `force_recreate` "
                        f"parameter to `True`."
                    )
                    raise QdrantException(msg)
                current_vector_config = current_vector_config.get(vector_name)  # type: ignore[assignment]
            elif isinstance(current_vector_config, dict) and vector_name is None:
                msg = (
                    f"Existing Qdrant collection {collection_name} uses named vectors. "
                    f"If you want to reuse it, please set `vector_name` to any of the "
                    f"existing named vectors: "
                    f"{', '.join(current_vector_config.keys())}."
                    f"If you want to recreate the collection, set `force_recreate` "
                    f"parameter to `True`."
                )
                raise QdrantException(msg)
            elif (
                not isinstance(current_vector_config, dict) and vector_name is not None
            ):
                msg = (
                    f"Existing Qdrant collection {collection_name} doesn't use named "
                    f"vectors. If you want to reuse it, please set `vector_name` to "
                    f"`None`. If you want to recreate the collection, set "
                    f"`force_recreate` parameter to `True`."
                )
                raise QdrantException(msg)
            if not isinstance(current_vector_config, models.VectorParams):
                msg = (
                    "Expected current_vector_config to be an instance of "
                    f"models.VectorParams, but got {type(current_vector_config)}"
                )
                raise ValueError(msg)

            # Check if the vector configuration has the same dimensionality.
            if current_vector_config.size != vector_size:
                msg = (
                    f"Existing Qdrant collection is configured for vectors with "
                    f"{current_vector_config.size} "
                    f"dimensions. Selected embeddings are {vector_size}-dimensional. "
                    f"If you want to recreate the collection, set `force_recreate` "
                    f"parameter to `True`."
                )
                raise QdrantException(msg)

            current_distance_func = (
                current_vector_config.distance.name.upper()  # type: ignore[union-attr]
            )
            if current_distance_func != distance_func:
                msg = (
                    f"Existing Qdrant collection is configured for "
                    f"{current_vector_config.distance} "  # type: ignore[union-attr]
                    f"similarity. Please set `distance_func` parameter to "
                    f"`{distance_func}` if you want to reuse it. If you want to "
                    f"recreate the collection, set `force_recreate` parameter to "
                    f"`True`."
                )
                raise QdrantException(msg)
        else:
            vectors_config = models.VectorParams(
                size=vector_size,
                distance=models.Distance[distance_func],
                on_disk=on_disk,
            )

            # If vector name was provided, we're going to use the named vectors feature
            # with just a single vector.
            if vector_name is not None:
                vectors_config = {  # type: ignore[assignment]
                    vector_name: vectors_config,
                }

            client.create_collection(
                collection_name=collection_name,
                vectors_config=vectors_config,
                shard_number=shard_number,
                replication_factor=replication_factor,
                write_consistency_factor=write_consistency_factor,
                on_disk_payload=on_disk_payload,
                hnsw_config=hnsw_config,
                optimizers_config=optimizers_config,
                wal_config=wal_config,
                quantization_config=quantization_config,
                init_from=init_from,
                timeout=timeout,  # type: ignore[arg-type]
            )
        return cls(
            client=client,
            collection_name=collection_name,
            embeddings=embedding,
            content_payload_key=content_payload_key,
            metadata_payload_key=metadata_payload_key,
            distance_strategy=distance_func,
            vector_name=vector_name,
            async_client=async_client,
        )