def read_metadata(self) -> Metadata:
        from safetensors import safe_open  # type: ignore[import]
        from safetensors.torch import _getdtype  # type: ignore[import]

        state_dict_metadata: dict[str, TensorStorageMetadata] = {}
        storage_data: dict[MetadataIndex, _HFStorageInfo] = {}

        safetensors_files = []
        for file in self.fs.ls(self.path):
            if file.endswith(SUFFIX):
                safetensors_files.append(file)

        for safetensor_file in safetensors_files:
            with safe_open(safetensor_file, framework="pt") as f:
                keys = f.keys()
                extra_metadata = f.metadata()

                dcp_sharding_info = None
                if extra_metadata and extra_metadata.get(CUSTOM_METADATA_KEY):
                    dcp_sharding_info = json.loads(
                        extra_metadata.get(CUSTOM_METADATA_KEY)
                    )

                for key in keys:
                    shape = f.get_slice(key).get_shape()
                    dtype = f.get_slice(key).get_dtype()
                    # construct state_dict_metadata
                    if dcp_sharding_info is not None:
                        offset = dcp_sharding_info[key][SAVED_OFFSETS_KEY]
                    else:
                        offset = [0] * len(shape)

                    if key not in state_dict_metadata:
                        state_dict_metadata[key] = TensorStorageMetadata(
                            properties=TensorProperties(dtype=_getdtype(dtype)),
                            size=torch.Size(
                                [saved + offset for saved, offset in zip(shape, offset)]
                            ),
                            chunks=[
                                ChunkStorageMetadata(
                                    offsets=torch.Size(offset),
                                    sizes=torch.Size(shape),
                                )
                            ],
                        )
                    else:
                        state_dict_metadata[key].chunks.append(
                            ChunkStorageMetadata(
                                torch.Size(offset), sizes=torch.Size(shape)
                            )
                        )
                        size = list(state_dict_metadata[key].size)
                        for i in range(len(size)):
                            size[i] = max(size[i], shape[i] + offset[i])
                        state_dict_metadata[key].size = torch.Size(size)

                    # construct storage data
                    if dcp_sharding_info is not None:
                        metadata_index = MetadataIndex(
                            fqn=key, offset=dcp_sharding_info[key][SAVED_OFFSETS_KEY]
                        )
                    else:
                        metadata_index = MetadataIndex(fqn=key, offset=[0] * len(shape))
                    storage_data[metadata_index] = _HFStorageInfo(
                        relative_path=safetensor_file,
                        shape=torch.Size(shape),
                        dtype=_getdtype(dtype),
                    )

        metadata = Metadata(
            state_dict_metadata=state_dict_metadata,  # type: ignore[arg-type]
            storage_data=storage_data,
        )

        if getattr(metadata, "storage_meta", None) is None:
            metadata.storage_meta = StorageMeta()
        metadata.storage_meta.load_id = self.load_id  # type: ignore[union-attr]

        return metadata