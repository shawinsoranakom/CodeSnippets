def forward(self, predicts, batch):
        loss_dict = dict()

        for idx, pair in enumerate(self.model_name_pairs):
            out1 = predicts[pair[0]]
            out2 = predicts[pair[1]]
            if self.key is not None:
                out1 = out1[self.key]
                out2 = out2[self.key]
            if self.maps_name is None:
                if self.multi_head:
                    # for nrtr dml loss
                    max_len = batch[3].max()
                    tgt = batch[2][:, 1 : 2 + max_len]  # [batch_size, max_len + 1]

                    tgt = tgt.reshape([-1])  # batch_size * (max_len + 1)
                    non_pad_mask = paddle.not_equal(
                        tgt, paddle.zeros(tgt.shape, dtype=tgt.dtype)
                    )  # batch_size * (max_len + 1)

                    loss = super().forward(
                        out1[self.dis_head], out2[self.dis_head], tgt, non_pad_mask
                    )  # [batch_size, max_len + 1, num_char]
                else:
                    loss = super().forward(out1, out2)
                if isinstance(loss, dict):
                    for key in loss:
                        loss_dict["{}_{}_{}_{}".format(key, pair[0], pair[1], idx)] = (
                            loss[key]
                        )
                else:
                    loss_dict["{}_{}".format(self.name, idx)] = loss
            else:
                outs1 = self._slice_out(out1)
                outs2 = self._slice_out(out2)
                for _c, k in enumerate(outs1.keys()):
                    loss = super().forward(outs1[k], outs2[k])
                    if isinstance(loss, dict):
                        for key in loss:
                            loss_dict[
                                "{}_{}_{}_{}_{}".format(
                                    key, pair[0], pair[1], self.maps_name, idx
                                )
                            ] = loss[key]
                    else:
                        loss_dict[
                            "{}_{}_{}".format(self.name, self.maps_name[_c], idx)
                        ] = loss

        loss_dict = _sum_loss(loss_dict)

        return loss_dict