def test_create_txt_slices_jsonl(
    hf_tokenizer: PreTrainedTokenizerBase, tmp_path: Path
) -> None:
    """Test that create_txt_slices_jsonl produces valid JSONL for CustomDataset."""
    txt_path = tmp_path / "input.txt"
    jsonl_path = tmp_path / "input.txt.jsonl"

    txt_path.write_text(text_content)

    create_txt_slices_jsonl(
        input_path=str(txt_path),
        output_path=str(jsonl_path),
        tokenizer_name="gpt2",
        num_prompts=10,
        input_len=10,
        output_len=10,
    )

    # Verify the JSONL file is valid and has the expected structure
    records = [json.loads(line) for line in jsonl_path.read_text().splitlines()]

    assert len(records) == 10
    for record in records:
        assert "prompt" in record
        assert "output_tokens" in record
        assert isinstance(record["prompt"], str)
        assert record["output_tokens"] == 10

    # Verify the JSONL file can be loaded by CustomDataset
    dataset = CustomDataset(dataset_path=str(jsonl_path))
    samples = dataset.sample(
        tokenizer=hf_tokenizer,
        num_requests=10,
        output_len=10,
        skip_chat_template=True,
    )

    assert len(samples) == 10
    assert all(sample.expected_output_len == 10 for sample in samples)