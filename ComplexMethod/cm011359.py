def finish(self, metadata: Metadata, results: list[list[WriteResult]]) -> None:
        if self.save_distributed and not self.enable_consolidation:
            # if we are saving distributed, without consolidating,
            # then we have no metadata to write because a metadata
            # file with fqn to file mapping doesn't make sense
            # in this case, because fqns will be in multiple files
            logger.info("Not consolidating sharded checkpoint in finish step.")
            return
        if self.save_distributed:
            fqn_to_index_mapping: dict[str, int] = (
                self.fqn_to_index_mapping
                if self.fqn_to_index_mapping is not None
                else dict.fromkeys(metadata.state_dict_metadata.keys(), 1)
            )

            return consolidate_safetensors_files(
                input_dir=str(self.path),
                output_dir=self.consolidated_output_path,  # type: ignore[arg-type]
                num_threads=self.thread_count_consolidation,
                fqn_to_index_mapping=fqn_to_index_mapping,
            )

        # writing a model.index.safetensors.json file with fqn to file mapping
        # for the rank-0 checkpointing case
        metadata_to_write = {}
        storage_md = {}
        total_size = 0
        for wr_list in results:
            storage_md.update(
                {wr.index.fqn: wr.storage_data.relative_path for wr in wr_list}
            )
            total_size += sum([wr.storage_data.length for wr in wr_list])
        metadata_to_write["metadata"] = {"total_size": total_size}
        metadata_to_write["weight_map"] = storage_md

        metadata_path = self.fs.concat_path(self.path, f"{_metadata_fn}")
        with self.fs.create_stream(metadata_path, "w") as metadata_file:
            json.dump(metadata_to_write, metadata_file, indent=2)