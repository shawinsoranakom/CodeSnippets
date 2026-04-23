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