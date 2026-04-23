def test_packing_sdpa(tmp_path):
    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
    model, batch, trainer, llama_mod = _build_packed_training_setup(tmp_path, device)

    assert "packed_seq_lengths" in batch
    assert "attention_mask" not in batch
    assert batch["packed_seq_lengths"].dtype == torch.int32

    total_tokens = batch["input_ids"].size(-1)
    assert int(batch["packed_seq_lengths"].sum().item()) == total_tokens

    packed_tokens = int(batch["packed_seq_lengths"].sum().item())
    assert "position_ids" in batch
    flat_positions = batch["position_ids"].reshape(-1)[:packed_tokens]
    expected_positions = torch.cat(
        [
            torch.arange(length, dtype = torch.long)
            for length in batch["packed_seq_lengths"].tolist()
        ]
    )
    assert torch.equal(flat_positions.cpu(), expected_positions)
    inputs = _trim_batch_to_total_tokens(batch, packed_tokens)

    seq_info = llama_mod.get_packed_info_from_kwargs(
        {"packed_seq_lengths": batch["packed_seq_lengths"]},
        inputs["input_ids"].device,
    )
    assert seq_info is not None

    original_mask = attention_dispatch_utils.build_sdpa_packed_attention_mask
    mask_calls = []
    captured_loss_labels = {}

    def _capture_mask(seq_info, dtype, device, *, sliding_window = None):
        mask_calls.append(tuple(seq_info[0].tolist()))
        return original_mask(
            seq_info,
            dtype = dtype,
            device = device,
            sliding_window = sliding_window,
        )

    def _capture_loss(*, logits, labels, **loss_kwargs):
        captured_loss_labels["labels"] = labels.detach().to("cpu")
        return torch.zeros((), device = logits.device, dtype = logits.dtype)

    with ExitStack() as stack:
        stack.enter_context(
            patch.object(attention_dispatch_utils, "HAS_FLASH_ATTENTION", False)
        )
        stack.enter_context(
            patch.object(attention_dispatch_utils, "HAS_XFORMERS", False)
        )
        stack.enter_context(
            patch.object(
                attention_dispatch_utils,
                "build_sdpa_packed_attention_mask",
                side_effect = _capture_mask,
            )
        )
        stack.enter_context(
            patch.object(
                llama_mod,
                "fast_cross_entropy_loss",
                side_effect = _capture_loss,
            )
        )
        with torch.no_grad():
            outputs = model(**inputs)

    assert mask_calls, "SDPA packed mask was not constructed"
    assert outputs.loss is not None
    assert "labels" in captured_loss_labels
    flat_loss_labels = captured_loss_labels["labels"].reshape(-1)
    boundaries = (
        torch.cumsum(
            batch["packed_seq_lengths"].to(device = "cpu", dtype = torch.long), dim = 0
        )
        - 1
    )
    for idx in boundaries.tolist():
        assert flat_loss_labels[idx].item() == -100
    assert torch.any(flat_loss_labels != -100)

    if hasattr(trainer, "accelerator"):
        trainer.accelerator.free_memory()