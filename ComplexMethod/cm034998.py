def __call__(self, preds, label=None, *args, **kwargs):
        # if seq_outputs is not None:
        if isinstance(preds, tuple) or isinstance(preds, list):
            cnt_outputs, seq_outputs = preds
            if isinstance(seq_outputs, paddle.Tensor):
                seq_outputs = seq_outputs.numpy()
            preds_idx = seq_outputs.argmax(axis=2)
            preds_prob = seq_outputs.max(axis=2)
            text = self.decode(preds_idx, preds_prob, is_remove_duplicate=False)

            if label is None:
                return text
            label = self.decode(label, is_remove_duplicate=False)
            return text, label

        else:
            cnt_outputs = preds
            if isinstance(cnt_outputs, paddle.Tensor):
                cnt_outputs = cnt_outputs.numpy()
            cnt_length = []
            for lens in cnt_outputs:
                length = round(np.sum(lens))
                cnt_length.append(length)
            if label is None:
                return cnt_length
            label = self.decode(label, is_remove_duplicate=False)
            length = [len(res[0]) for res in label]
            return cnt_length, length