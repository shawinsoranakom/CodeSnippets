 def create_packed_sequences(examples):
        # Flatten all sequences
        all_tokens = []
        for input_ids in examples["input_ids"]:
            all_tokens.extend(input_ids)

        # Split into sequences of seq_len + 1 (for input + label)
        num_sequences = len(all_tokens) // (seq_len + 1)
        packed_input_ids = []
        packed_labels = []

        for i in range(num_sequences):
            start_idx = i * (seq_len + 1)
            end_idx = start_idx + (seq_len + 1)
            # Get the full sequence
            full_sequence = all_tokens[start_idx:end_idx]
            # For input_ids, remove the last token
            packed_input_ids.append(full_sequence[:-1])
            # For labels, remove the first token
            packed_labels.append(full_sequence[1:])

        return {"input_ids": packed_input_ids, "labels": packed_labels}
