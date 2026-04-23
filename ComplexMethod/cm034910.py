def forward(self, inputs, targets=None):
        if self.is_next == True:
            fea = inputs
            batch_size = fea.shape[0]
        else:
            fea = inputs[-1]
            batch_size = fea.shape[0]
            if self.use_attn:
                fea = fea + self.cross_atten(fea)
            # reshape
            fea = paddle.reshape(fea, [fea.shape[0], fea.shape[1], -1])
            fea = fea.transpose([0, 2, 1])  # (NTC)(batch, width, channels)

        hidden = paddle.zeros((batch_size, self.hidden_size))
        structure_preds = paddle.zeros(
            (batch_size, self.max_text_length + 1, self.num_embeddings)
        )
        loc_preds = paddle.zeros(
            (batch_size, self.max_text_length + 1, self.loc_reg_num)
        )
        structure_preds.stop_gradient = True
        loc_preds.stop_gradient = True

        if self.training and targets is not None:
            structure = targets[0]
            max_len = targets[-2].max().astype("int32")
            for i in range(max_len + 1):
                hidden, structure_step, loc_step = self._decode(
                    structure[:, i], fea, hidden
                )
                structure_preds[:, i, :] = structure_step
                loc_preds[:, i, :] = loc_step
            structure_preds = structure_preds[:, : max_len + 1]
            loc_preds = loc_preds[:, : max_len + 1]
        else:
            structure_ids = paddle.zeros(
                (batch_size, self.max_text_length + 1), dtype="int32"
            )
            pre_chars = paddle.zeros(shape=[batch_size], dtype="int32")
            max_text_length = paddle.to_tensor(self.max_text_length)
            for i in range(max_text_length + 1):
                hidden, structure_step, loc_step = self._decode(pre_chars, fea, hidden)
                pre_chars = structure_step.argmax(axis=1, dtype="int32")
                structure_preds[:, i, :] = structure_step
                loc_preds[:, i, :] = loc_step

                structure_ids[:, i] = pre_chars
                if (structure_ids == self.eos).any(-1).all():
                    break
        if not self.training:
            structure_preds = F.softmax(structure_preds[:, : i + 1])
            loc_preds = loc_preds[:, : i + 1]
        return {"structure_probs": structure_preds, "loc_preds": loc_preds}