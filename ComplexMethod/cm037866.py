def gguf_quant_weights_iterator_multi(
    gguf_files: list[str], gguf_to_hf_name_map: dict[str, str]
) -> Generator[tuple[str, torch.Tensor], None, None]:
    """
    Iterate over the quant weights across multiple GGUF shard files
    and convert them to torch tensors.

    Like gguf_quant_weights_iterator, we yield all weight types first
    before yielding any weights data to avoid issues with packed layers
    that have different quant types.
    """
    readers = [gguf.GGUFReader(f) for f in gguf_files]

    # First pass: yield all weight types across all shards
    for reader in readers:
        for tensor in reader.tensors:
            if tensor.name in gguf_to_hf_name_map:
                weight_type = tensor.tensor_type
                name = gguf_to_hf_name_map[tensor.name]
                if weight_type.name not in ("F32", "BF16", "F16"):
                    weight_type_name = name.replace("weight", "qweight_type")
                    weight_type = torch.tensor(weight_type)
                    yield weight_type_name, weight_type

    # Second pass: yield all weight data across all shards
    for reader in readers:
        for tensor in reader.tensors:
            if tensor.name in gguf_to_hf_name_map:
                weight = tensor.data
                weight_type = tensor.tensor_type
                name = gguf_to_hf_name_map[tensor.name]
                if weight_type.name not in ("F32", "BF16", "F16"):
                    name = name.replace("weight", "qweight")
                if weight_type.name == "BF16" and tensor.data.dtype == np.uint8:
                    weight = weight.view(np.uint16)
                    if reader.byte_order == "S":
                        weight = weight.byteswap()
                    param = torch.tensor(weight).view(torch.bfloat16)
                else:
                    param = torch.tensor(weight)
                yield name, param