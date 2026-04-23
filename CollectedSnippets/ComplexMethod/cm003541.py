def forward(
        self,
        hidden_states: tuple[torch.FloatTensor],
        attention_mask: torch.FloatTensor | None = None,
        output_attentions: bool | None = False,
    ) -> tuple[torch.FloatTensor, torch.FloatTensor | None]:
        if not self.local:
            self_outputs = self.self(hidden_states, hidden_states, attention_mask, output_attentions)
            attention_output = self_outputs[0]
        else:
            from_seq_length = to_seq_length = hidden_states.shape[1]
            from_tensor = to_tensor = hidden_states

            # Create chunks (windows) that we will attend *from* and then concatenate them.
            from_chunks = []
            if self.first_position_attends_to_all:
                from_chunks.append((0, 1))
                # We must skip this first position so that our output sequence is the
                # correct length (this matters in the *from* sequence only).
                from_start = 1
            else:
                from_start = 0
            for chunk_start in range(from_start, from_seq_length, self.attend_from_chunk_stride):
                chunk_end = min(from_seq_length, chunk_start + self.attend_from_chunk_width)
                from_chunks.append((chunk_start, chunk_end))

            # Determine the chunks (windows) that will attend *to*.
            to_chunks = []
            if self.first_position_attends_to_all:
                to_chunks.append((0, to_seq_length))
            for chunk_start in range(0, to_seq_length, self.attend_to_chunk_stride):
                chunk_end = min(to_seq_length, chunk_start + self.attend_to_chunk_width)
                to_chunks.append((chunk_start, chunk_end))

            if len(from_chunks) != len(to_chunks):
                raise ValueError(
                    f"Expected to have same number of `from_chunks` ({from_chunks}) and "
                    f"`to_chunks` ({from_chunks}). Check strides."
                )

            # next, compute attention scores for each pair of windows and concatenate
            attention_output_chunks = []
            attention_probs_chunks = []
            for (from_start, from_end), (to_start, to_end) in zip(from_chunks, to_chunks):
                from_tensor_chunk = from_tensor[:, from_start:from_end, :]
                to_tensor_chunk = to_tensor[:, to_start:to_end, :]
                # `attention_mask`: <float>[batch_size, from_seq, to_seq]
                # `attention_mask_chunk`: <float>[batch_size, from_seq_chunk, to_seq_chunk]
                attention_mask_chunk = attention_mask[:, from_start:from_end, to_start:to_end]
                if self.always_attend_to_first_position:
                    cls_attention_mask = attention_mask[:, from_start:from_end, 0:1]
                    attention_mask_chunk = torch.cat([cls_attention_mask, attention_mask_chunk], dim=2)

                    cls_position = to_tensor[:, 0:1, :]
                    to_tensor_chunk = torch.cat([cls_position, to_tensor_chunk], dim=1)

                attention_outputs_chunk = self.self(
                    from_tensor_chunk, to_tensor_chunk, attention_mask_chunk, output_attentions
                )
                attention_output_chunks.append(attention_outputs_chunk[0])
                if output_attentions:
                    attention_probs_chunks.append(attention_outputs_chunk[1])

            attention_output = torch.cat(attention_output_chunks, dim=1)

        attention_output = self.output(attention_output, hidden_states)
        outputs = (attention_output,)
        if not self.local:
            outputs = outputs + self_outputs[1:]  # add attentions if we output them
        else:
            outputs = outputs + tuple(attention_probs_chunks)  # add attentions if we output them
        return outputs