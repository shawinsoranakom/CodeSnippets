def consolidate_safetensors_files_on_every_rank(
    input_dir: str,
    output_dir: str,
    fqn_to_index_mapping: dict[str, int],
    num_threads: int = 1,
    process_group: dist.ProcessGroup | None = None,
) -> None:
    """
    Consolidate sharded safetensors files across multiple ranks, with each rank handling a subset of output files.

    This function distributes the consolidation work by assigning output files to different ranks.
    All tensors with the same index in fqn_to_index_mapping are processed by the same rank,
    as they belong to the same output file.

    If process_group is provided, rank and world_size will be derived from it. Otherwise,
    they will be automatically detected from the distributed environment if available.

    Args:
        input_dir: Directory containing sharded safetensors files
        output_dir: Directory where consolidated files will be written
        fqn_to_index_mapping: Mapping of tensor names to output file indices
        num_threads: Number of threads to use for parallel processing on each rank
        process_group: PyTorch distributed process group (default: None, will use default group)
    """

    start_time = time.time()
    # Derive rank and world_size from process_group or default distributed environment
    if dist.is_available() and dist.is_initialized():
        rank = dist.get_rank(group=process_group)
        world_size = dist.get_world_size(group=process_group)
    else:
        # Default to single process mode if distributed is not initialized
        rank = 0
        world_size = 1
        logger.warning(
            "Distributed environment not initialized. Running in single process mode."
        )
    logger.info(
        "Rank %d/%d: Consolidating safetensors files from %s to %s",
        rank,
        world_size,
        input_dir,
        output_dir,
    )

    # Find all unique indices in the mapping
    unique_indices = set(fqn_to_index_mapping.values())

    # Distribute indices across ranks
    indices_for_this_rank = []
    for idx in unique_indices:
        # Simple distribution: index % world_size == rank
        if idx % world_size == rank:
            indices_for_this_rank.append(idx)

    logger.info(
        "Rank %d: Assigned %d output files out of %d total files",
        rank,
        len(indices_for_this_rank),
        len(unique_indices),
    )

    # Filter the fqn_to_index_mapping to only include tensors for this rank
    filtered_mapping = {
        fqn: idx
        for fqn, idx in fqn_to_index_mapping.items()
        if idx in indices_for_this_rank
    }

    output_files_data: dict[str, _OutputFileData] = {}
    if filtered_mapping:
        # Convert index mapping to filename mapping
        max_index = max(unique_indices)
        filtered_filename_mapping = {}
        for fqn, idx in filtered_mapping.items():
            filename = _gen_file_name(idx, max_index)
            filtered_filename_mapping[fqn] = filename

        # Call the existing consolidation function with the filtered mapping
        output_files_data = _consolidate_safetensors_files(
            input_dir=input_dir,
            output_dir=output_dir,
            fqn_to_file_mapping=filtered_filename_mapping,
            num_threads=num_threads,
        )

    logger.info(
        "Rank %d: Done consolidating. Processed %d unique indices in %.2f secs.",
        rank,
        len(indices_for_this_rank),
        time.time() - start_time,
    )

    # Wait for all ranks to complete and gather output_files_data on rank 0
    if dist.is_available() and dist.is_initialized():
        gathered_output_files_data: list[dict[str, _OutputFileData]] | None = (
            [{} for _ in range(world_size)] if rank == 0 else None
        )
        dist.gather_object(
            output_files_data,
            gathered_output_files_data,
            dst=0,
            group=process_group,
        )

        if rank == 0:
            # Merge all output_files_data from all ranks
            all_output_files_data: dict[str, _OutputFileData] = {}
            if gathered_output_files_data is None:
                raise AssertionError
            for rank_data in gathered_output_files_data:
                all_output_files_data.update(rank_data)

            _write_overall_metadata_file(output_dir, all_output_files_data)
            logger.info("Rank 0: Wrote overall metadata file.")
            logger.info("Total time taken: %.2f secs.", time.time() - start_time)
        dist.barrier(group=process_group)