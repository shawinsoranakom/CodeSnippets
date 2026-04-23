def enable_sample_packing(
    model,
    trainer,
    *,
    sequence_lengths_key: str = "seq_lengths",
) -> None:
    """Enable runtime support for packed batches on an existing trainer."""
    if model is None or trainer is None:
        raise ValueError("model and trainer must not be None")

    mark_allow_overlength(model)

    if hasattr(trainer, "args") and hasattr(trainer.args, "remove_unused_columns"):
        trainer.args.remove_unused_columns = False

    collator = getattr(trainer, "data_collator", None)
    if collator is None or not hasattr(collator, "torch_call"):
        return
    if getattr(collator, "_unsloth_packing_wrapped", False):
        return

    if hasattr(collator, "padding_free"):
        collator.padding_free = True
    if hasattr(collator, "return_position_ids"):
        collator.return_position_ids = True

    original_torch_call = collator.torch_call

    def torch_call_with_lengths(examples: Sequence[dict]):
        batch = original_torch_call(examples)
        if examples and isinstance(examples[0], dict):
            seq_lengths: list[int] = []
            for example in examples:
                lengths = example.get(sequence_lengths_key)
                if isinstance(lengths, Iterable):
                    seq_lengths.extend(int(length) for length in lengths)
            # Fallback: infer lengths from tokenized inputs when metadata is absent
            if not seq_lengths:
                for example in examples:
                    ids = example.get("input_ids")
                    if isinstance(ids, Iterable):
                        seq_lengths.append(len(ids))
            if seq_lengths:
                batch["packed_seq_lengths"] = torch.tensor(
                    seq_lengths, dtype = torch.int32
                )
                if "attention_mask" in batch:
                    batch.pop("attention_mask")
        return batch

    collator.torch_call = torch_call_with_lengths
    collator._unsloth_packing_wrapped = True