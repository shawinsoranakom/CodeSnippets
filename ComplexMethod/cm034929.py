def forward_test(self, memory, max_length=None):
        testing = max_length is None
        max_length = (
            self.max_label_length
            if max_length is None
            else min(max_length, self.max_label_length)
        )
        bs = memory.shape[0]
        num_steps = max_length + 1

        pos_queries = self.pos_queries[:, :num_steps].expand(shape=[bs, -1, -1])
        tgt_mask = query_mask = paddle.triu(
            x=paddle.full(shape=(num_steps, num_steps), fill_value=float("-inf")),
            diagonal=1,
        )
        if self.decode_ar:
            tgt_in = paddle.full(shape=(bs, num_steps), fill_value=self.pad_id).astype(
                "int64"
            )
            tgt_in[:, (0)] = self.bos_id

            logits = []
            for i in range(paddle.to_tensor(num_steps)):
                j = i + 1
                tgt_out = self.decode(
                    tgt_in[:, :j],
                    memory,
                    tgt_mask[:j, :j],
                    tgt_query=pos_queries[:, i:j],
                    tgt_query_mask=query_mask[i:j, :j],
                )
                p_i = self.head(tgt_out)
                logits.append(p_i)
                if j < num_steps:
                    tgt_in[:, (j)] = p_i.squeeze().argmax(axis=-1)
                    if (
                        testing
                        and (tgt_in == self.eos_id)
                        .astype("bool")
                        .any(axis=-1)
                        .astype("bool")
                        .all()
                    ):
                        break
            logits = paddle.concat(x=logits, axis=1)
        else:
            tgt_in = paddle.full(shape=(bs, 1), fill_value=self.bos_id).astype("int64")
            tgt_out = self.decode(tgt_in, memory, tgt_query=pos_queries)
            logits = self.head(tgt_out)
        if self.refine_iters:
            temp = paddle.triu(
                x=paddle.ones(shape=[num_steps, num_steps], dtype="bool"), diagonal=2
            )
            posi = paddle.where(temp == True)
            query_mask[posi] = 0
            bos = paddle.full(shape=(bs, 1), fill_value=self.bos_id).astype("int64")
            for i in range(self.refine_iters):
                tgt_in = paddle.concat(x=[bos, logits[:, :-1].argmax(axis=-1)], axis=1)
                tgt_padding_mask = (tgt_in == self.eos_id).astype(dtype="int32")
                tgt_padding_mask = tgt_padding_mask.cpu()
                tgt_padding_mask = tgt_padding_mask.cumsum(axis=-1) > 0
                tgt_padding_mask = (
                    tgt_padding_mask.cuda().astype(dtype="float32") == 1.0
                )
                tgt_out = self.decode(
                    tgt_in,
                    memory,
                    tgt_mask,
                    tgt_padding_mask,
                    tgt_query=pos_queries,
                    tgt_query_mask=query_mask[:, : tgt_in.shape[1]],
                )
                logits = self.head(tgt_out)

        # transfer to probability
        logits = F.softmax(logits, axis=-1)

        final_output = {"predict": logits}

        return final_output