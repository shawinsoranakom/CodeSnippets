def _detect_field(
    tensors: list[torch.Tensor],
    mm_processor: BaseMultiModalProcessor,
):
    first_item = tensors[0]
    hidden_size = mm_processor.info.ctx.model_config.get_inputs_embeds_size()

    if (
        len(tensors) == 1
        and first_item.ndim == 3
        and first_item.shape[0] == 1
        and first_item.shape[-1] == hidden_size
    ):
        logger.warning(
            "Batched multi-modal embedding inputs are deprecated for Chat API. "
            "Please pass a separate content part for each multi-modal item."
        )
        return _BatchedSingleItemField(batch_size=1)

    first_shape = first_item.shape
    if all(t.shape == first_shape for t in tensors):
        return MultiModalBatchedField()

    size_per_item = [len(tensor) for tensor in tensors]
    slice_idxs = [0, *accumulate(size_per_item)]
    slices = [
        (slice(slice_idxs[i], slice_idxs[i + 1]),) for i in range(len(size_per_item))
    ]
    return MultiModalFlatField(slices=slices)