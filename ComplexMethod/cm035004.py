def __call__(self, preds, label=None, length=None, *args, **kwargs):
        if len(preds) == 2:  # eval mode
            text_pre, x = preds
            b = text_pre.shape[1]
            lenText = self.max_text_length
            nsteps = self.max_text_length

            if not isinstance(text_pre, paddle.Tensor):
                text_pre = paddle.to_tensor(text_pre, dtype="float32")

            out_res = paddle.zeros(shape=[lenText, b, self.nclass], dtype=x.dtype)
            out_length = paddle.zeros(shape=[b], dtype=x.dtype)
            now_step = 0
            for _ in range(nsteps):
                if 0 in out_length and now_step < nsteps:
                    tmp_result = text_pre[now_step, :, :]
                    out_res[now_step] = tmp_result
                    tmp_result = tmp_result.topk(1)[1].squeeze(axis=1)
                    for j in range(b):
                        if out_length[j] == 0 and tmp_result[j] == 0:
                            out_length[j] = now_step + 1
                    now_step += 1
            for j in range(0, b):
                if int(out_length[j]) == 0:
                    out_length[j] = nsteps
            start = 0
            output = paddle.zeros(
                shape=[int(out_length.sum()), self.nclass], dtype=x.dtype
            )
            for i in range(0, b):
                cur_length = int(out_length[i])
                output[start : start + cur_length] = out_res[0:cur_length, i, :]
                start += cur_length
            net_out = output
            length = out_length

        else:  # train mode
            net_out = preds[0]
            length = length
            net_out = paddle.concat([t[:l] for t, l in zip(net_out, length)])
        text = []
        if not isinstance(net_out, paddle.Tensor):
            net_out = paddle.to_tensor(net_out, dtype="float32")
        net_out = F.softmax(net_out, axis=1)
        for i in range(0, length.shape[0]):
            if i == 0:
                start_idx = 0
                end_idx = int(length[i])
            else:
                start_idx = int(length[:i].sum())
                end_idx = int(length[:i].sum() + length[i])
            preds_idx = net_out[start_idx:end_idx].topk(1)[1][:, 0].tolist()
            preds_text = "".join(
                [
                    (
                        self.character[idx - 1]
                        if idx > 0 and idx <= len(self.character)
                        else ""
                    )
                    for idx in preds_idx
                ]
            )
            preds_prob = net_out[start_idx:end_idx].topk(1)[0][:, 0]
            preds_prob = paddle.exp(
                paddle.log(preds_prob).sum() / (preds_prob.shape[0] + 1e-6)
            )
            text.append((preds_text, float(preds_prob)))
        if label is None:
            return text
        label = self.decode(label)
        return text, label