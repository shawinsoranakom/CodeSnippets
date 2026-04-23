def decode(
            self,
            text_index,
            text_prob=None,
            is_remove_duplicate=False,
            return_word_box=False,
    ):
        """ convert text-index into text-label. """
        result_list = []
        batch_size = text_index.shape[0]
        blank_word = self.get_ignored_tokens()[0]
        for batch_idx in range(batch_size):
            probs = None if text_prob is None else np.array(text_prob[batch_idx])
            sequence = text_index[batch_idx]

            final_mask = sequence != blank_word
            if is_remove_duplicate:
                duplicate_mask = np.insert(sequence[1:] != sequence[:-1], 0, True)
                final_mask &= duplicate_mask

            sequence = sequence[final_mask]
            probs = None if probs is None else probs[final_mask]
            text = "".join(self.character[sequence])

            if text_prob is not None and probs is not None and len(probs) > 0:
                mean_conf = np.mean(probs)
            else:
                # 如果没有提供概率或最终结果为空，则默认置信度为1.0
                mean_conf = 1.0
            result_list.append((text, mean_conf))
        return result_list