def gguf_quant_weights_iterator(
    gguf_file: str | Path, gguf_to_hf_name_map: dict[str, str]
) -> Generator[tuple[str, torch.Tensor], None, None]:
    """
    Iterate over the quant weights in the model gguf files and convert
    them to torch tensors.
    Be careful of the order of yielding weight types and weights data,
    we have to yield all weight types first before yielding any weights.
    Otherwise it would cause issue when loading weights with for packed
    layer with different quant types.
    """

    reader = gguf.GGUFReader(gguf_file)

    for tensor in reader.tensors:
        if tensor.name in gguf_to_hf_name_map:
            weight_type = tensor.tensor_type
            name = gguf_to_hf_name_map[tensor.name]

            if weight_type.name not in ("F32", "BF16", "F16"):
                weight_type_name = name.replace("weight", "qweight_type")
                weight_type = torch.tensor(weight_type)
                yield weight_type_name, weight_type

    for tensor in reader.tensors:
        if tensor.name in gguf_to_hf_name_map:
            weight = tensor.data
            weight_type = tensor.tensor_type
            name = gguf_to_hf_name_map[tensor.name]
            if weight_type.name not in ("F32", "BF16", "F16"):
                name = name.replace("weight", "qweight")
            if weight_type.name == "BF16" and tensor.data.dtype == np.uint8:
                # BF16 is currently the only "quantization" type that isn't
                # actually quantized but is read as a raw byte tensor.
                # Reinterpret as `torch.bfloat16` tensor.
                weight = weight.view(np.uint16)
                if reader.byte_order == "S":
                    # GGUF endianness != system endianness
                    weight = weight.byteswap()
                param = torch.tensor(weight).view(torch.bfloat16)
            else:
                param = torch.tensor(weight)
            yield name, param