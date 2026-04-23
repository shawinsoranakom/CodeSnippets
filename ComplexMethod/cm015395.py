def test_ddp_packed_sequence(self):
        """
        Tests that DDP with ``device_ids`` specified can run a forward and
        backward pass with ``PackedSequence`` s with parity compared to a local
        version of the model.
        """
        store = c10d.FileStore(self.file_name, self.world_size)
        process_group = dist.init_process_group(
            "nccl",
            world_size=self.world_size,
            rank=self.rank,
            store=store,
        )
        seqs = ["sequence_sequence", "seq", "sequence"]
        vocab = ["<pad>"] + sorted({ch for seq in seqs for ch in seq})
        vectorized_seqs = [[vocab.index(tok) for tok in seq] for seq in seqs]
        # Set the seed to make the embedding and LSTM deterministic (even
        # across ranks since DDP broadcasts parameters from rank 0)
        torch.manual_seed(0)
        embed = nn.Embedding(len(vocab), 4)  # keep on CPU
        lstm = nn.LSTM(input_size=4, hidden_size=2, batch_first=True).to(self.rank)
        lstm_ddp = DistributedDataParallel(
            copy.deepcopy(lstm),
            device_ids=[self.rank],
            process_group=process_group,
        )
        for p1, p2 in zip(lstm.parameters(), lstm_ddp.module.parameters()):
            self.assertEqual(p1, p2)
        seq_lengths = torch.LongTensor(list(map(len, vectorized_seqs)))
        seq_tensor = torch.Tensor(
            torch.zeros((len(vectorized_seqs), seq_lengths.max()))
        ).long()
        for i, (seq, seq_len) in enumerate(zip(vectorized_seqs, seq_lengths)):
            seq_tensor[i, :seq_len] = torch.LongTensor(seq)
        seq_lengths, permutation_idx = seq_lengths.sort(0, descending=True)
        seq_tensor = seq_tensor[permutation_idx]
        embedded_seq_tensor = embed(seq_tensor)
        packed_input = torch.nn.utils.rnn.pack_padded_sequence(
            embedded_seq_tensor,
            seq_lengths,
            batch_first=True,
        )
        packed_input_ddp = torch.nn.utils.rnn.pack_padded_sequence(
            embedded_seq_tensor.detach().clone(),
            seq_lengths,
            batch_first=True,
        )
        # Move the input to GPU explicitly for the local model
        packed_output, (ht, ct) = lstm(packed_input.to(self.rank))
        # Let DDP move the input to GPU internally
        packed_output_ddp, (ht_ddp, ct_ddp) = lstm_ddp(packed_input_ddp)
        self.assertEqual(packed_output.data, packed_output_ddp.data)
        self.assertEqual(ht, ht_ddp)
        self.assertEqual(ct, ct_ddp)
        packed_output.data.sum().backward()
        packed_output_ddp.data.sum().backward()
        for p1, p2 in zip(lstm.parameters(), lstm_ddp.parameters()):
            self.assertEqual(p1.grad, p2.grad)