def _parse_input_metadata(
    input_files_data: dict[str, _InputFileData],
    output_files_data: dict[str, _OutputFileData],
) -> None:
    """
    Parse metadata from input safetensors files to determine the full tensor shapes and types.

    This function analyzes the metadata from all input files to determine the complete shape
    of each tensor after consolidation. It updates the output_files_data with this information.

    Args:
        input_files_data: dict of metadata from input safetensors files
        output_files_data: Dictionary mapping output file paths to their metadata

    Raises:
        ValueError: If no DCP custom metadata is found in a safetensors file
    """

    from safetensors.torch import _getdtype  # type: ignore[import]

    # Dictionary to track the full size of each tensor across all shards
    fqn_to_size_mapping: dict[str, tuple[list[int], str]] = {}

    for file_data in input_files_data.values():
        safetensors_metadata = file_data.metadata
        dcp_sharding_info = _get_dcp_custom_metadata(safetensors_metadata)
        if not dcp_sharding_info:
            raise ValueError(
                "No DCP custom metadata found in safetensors file. The file must be saved with DCP to be consolidated."
            )

        for key, val in safetensors_metadata.items():
            if key == DEFAULT_EXTRA_METADATA_KEY:
                continue

            # Get the shape of this tensor shard and its offset in the full tensor
            sizes = val[SHAPE_KEY]
            offsets = dcp_sharding_info[key][SAVED_OFFSETS_KEY]

            if key not in fqn_to_size_mapping:
                # First time seeing this tensor - calculate its full size by adding offsets to dimensions
                cur_size = [size + offset for size, offset in zip(sizes, offsets)]
                fqn_to_size_mapping[key] = (cur_size, val[DTYPE_KEY])
            else:
                # We've seen this tensor before - update its size if this shard extends beyond current known dimensions
                cur_size = fqn_to_size_mapping[key][0]
                for i in range(len(sizes)):
                    cur_size[i] = max(cur_size[i], sizes[i] + offsets[i])

    # Now that we know the full size of each tensor, populate the output file data
    for fqn, tensor_info in fqn_to_size_mapping.items():
        tensor_size = tensor_info[0]
        dtype_str = tensor_info[1]
        for output_data in output_files_data.values():
            # Add this tensor to the output file if it's already assigned there
            if fqn in output_data.fqn_data:
                output_data.fqn_data[fqn] = _FqnData(
                    shape_in_file=tensor_size,
                    dtype_size=torch.finfo(_getdtype(dtype_str)).bits
                    // 8,  # Convert bits to bytes
                    dtype_str=dtype_str,
                )