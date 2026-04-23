def append_boxes(self, boxes, labels=None, mask=None):
        """Append box prompts to existing prompts.

        Args:
            boxes (torch.Tensor): Tensor of shape (N_new_boxes, B, 4) with normalized box coordinates.
            labels (torch.Tensor | None): Optional tensor of shape (N_new_boxes, B) with positive/negative labels.
            mask (torch.Tensor | None): Optional tensor of shape (B, N_new_boxes) for attention mask.
        """
        if self.box_embeddings is None:
            # First boxes - initialize
            self.box_embeddings = boxes
            bs = boxes.shape[1]
            box_seq_len = boxes.shape[0]

            if labels is None:
                labels = torch.ones(box_seq_len, bs, device=boxes.device, dtype=torch.long)
            if mask is None:
                mask = torch.zeros(bs, box_seq_len, device=boxes.device, dtype=torch.bool)

            self.box_labels = labels
            self.box_mask = mask
            return

        # Append to existing boxes
        bs = self.box_embeddings.shape[1]
        assert boxes.shape[1] == bs, f"Batch size mismatch: expected {bs}, got {boxes.shape[1]}"

        if labels is None:
            labels = torch.ones(boxes.shape[0], bs, device=boxes.device, dtype=torch.long)
        if mask is None:
            mask = torch.zeros(bs, boxes.shape[0], dtype=torch.bool, device=boxes.device)

        assert list(boxes.shape[:2]) == list(labels.shape[:2]), (
            f"Shape mismatch between boxes {boxes.shape} and labels {labels.shape}"
        )

        # Concatenate using the helper function
        self.box_labels, _ = concat_padded_sequences(
            self.box_labels.unsqueeze(-1), self.box_mask, labels.unsqueeze(-1), mask
        )
        self.box_labels = self.box_labels.squeeze(-1)
        self.box_embeddings, self.box_mask = concat_padded_sequences(self.box_embeddings, self.box_mask, boxes, mask)