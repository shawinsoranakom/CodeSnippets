def _write_item(
    transforms: _StorageWriterTransforms,
    stream: io.IOBase,
    data: io.BytesIO | torch.Tensor,
    write_item: WriteItem,
    storage_key: str,
    serialization_format: SerializationFormat,
) -> WriteResult:
    offset = stream.tell()

    (transform_to, transform_descriptors) = transforms.transform_save_stream(
        write_item, stream
    )

    if write_item.type == WriteItemType.BYTE_IO:
        if not isinstance(data, io.BytesIO):
            raise AssertionError("Data must be io.BytesIO for BYTE_IO write items")
        transform_to.write(data.getbuffer())
    else:
        if not isinstance(data, torch.Tensor):
            raise AssertionError(
                "Data must be torch.Tensor for non-BYTE_IO write items"
            )
        if data.device != torch.device("cpu"):
            raise AssertionError("Tensor must be on CPU device")
        if serialization_format == SerializationFormat.TORCH_SAVE:
            torch.save(data, transform_to)

    transform_to.close()

    if serialization_format == SerializationFormat.TORCH_SAVE or isinstance(
        data, io.BytesIO
    ):
        length = stream.tell() - offset
    else:
        length = data.numel() * data.element_size()

    # For consistency with earlier versions, leave this field out of the
    # metadata if there are no extensions.
    info_transform_descriptors = (
        None if len(transform_descriptors) == 0 else transform_descriptors
    )

    return WriteResult(
        index=write_item.index,
        size_in_bytes=length,
        storage_data=_StorageInfo(
            storage_key,
            offset,
            length,
            transform_descriptors=info_transform_descriptors,
        ),
    )