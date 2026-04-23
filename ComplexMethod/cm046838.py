def test_enable_sample_packing():
    model = _DummyModel()
    trainer = _DummyTrainer()

    enable_sample_packing(model, trainer)

    # model hierarchy should now allow packed overlength inputs
    assert getattr(model, "_unsloth_allow_packed_overlength") is True
    assert getattr(model.child, "_unsloth_allow_packed_overlength") is True

    collator = trainer.data_collator
    assert collator.return_position_ids is True
    assert getattr(collator, "_unsloth_packing_wrapped") is True

    examples = [
        {
            "input_ids": [0, 1, 2],
            "labels": [0, 1, 2],
            "seq_lengths": [2, 1],
        },
        {
            "input_ids": [3, 4, 5],
            "labels": [3, 4, 5],
            "seq_lengths": [3],
        },
    ]
    batch = collator.torch_call(examples)

    # packed lengths are aggregated into a single tensor
    assert "packed_seq_lengths" in batch
    assert torch.equal(
        batch["packed_seq_lengths"],
        torch.tensor([2, 1, 3], dtype = torch.int32),
    )

    assert batch["input_ids"].shape == (1, 6)
    expected_positions = torch.tensor([0, 1, 0, 0, 1, 2], dtype = torch.long)
    assert torch.equal(batch["position_ids"].view(-1)[:6], expected_positions)