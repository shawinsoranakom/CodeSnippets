def forward(self, predicts, batch):
        loss_dict = dict()
        for idx, pair in enumerate(self.model_name_pairs):
            out1 = predicts[pair[0]]
            out2 = predicts[pair[1]]
            attention_mask = batch[2]
            if self.key is not None:
                out1 = out1[self.key]
                out2 = out2[self.key]
                if self.index is not None:
                    out1 = out1[:, self.index, :, :]
                    out2 = out2[:, self.index, :, :]
                if attention_mask is not None:
                    max_len = attention_mask.shape[-1]
                    out1 = out1[:, :max_len]
                    out2 = out2[:, :max_len]
                out1 = out1.reshape([-1, out1.shape[-1]])
                out2 = out2.reshape([-1, out2.shape[-1]])
            if attention_mask is not None:
                active_output = (
                    attention_mask.reshape(
                        [
                            -1,
                        ]
                    )
                    == 1
                )
                out1 = out1[active_output]
                out2 = out2[active_output]

            loss = super().forward(out1, out2)
            if isinstance(loss, dict):
                for key in loss:
                    loss_dict["{}_{}nohu_{}".format(self.name, key, idx)] = loss[key]
            else:
                loss_dict["{}_{}_{}_{}".format(self.name, pair[0], pair[1], idx)] = loss
        return loss_dict