def _prepare_data(
        self, sentences: List[str]
    ) -> Tuple[List[str], List[int], List[int], List[int], List[List[str]]]:
        texts, model_query_ids, result_query_ids, sent_ids, partial_results = [], [], [], [], []
        for sent_id, sent in enumerate(sentences):
            sent_s = tranditional_to_simplified(sent)
            pypinyin_result = pinyin(sent_s, neutral_tone_with_five=True, style=Style.TONE3)
            partial_result = [None] * len(sent)
            polyphonic_indices: List[int] = []
            for i, char in enumerate(sent):
                if char in self.polyphonic_chars_new:
                    polyphonic_indices.append(i)
                elif char in self.monophonic_chars_dict:
                    partial_result[i] = self.style_convert_func(self.monophonic_chars_dict[char])
                elif char in self.char_bopomofo_dict:
                    partial_result[i] = pypinyin_result[i][0]
                else:
                    partial_result[i] = pypinyin_result[i][0]

            if polyphonic_indices:
                if self.polyphonic_context_chars > 0:
                    left = max(0, polyphonic_indices[0] - self.polyphonic_context_chars)
                    right = min(len(sent), polyphonic_indices[-1] + self.polyphonic_context_chars + 1)
                    sent_for_predict = sent[left:right]
                    query_offset = left
                else:
                    sent_for_predict = sent
                    query_offset = 0

                for index in polyphonic_indices:
                    texts.append(sent_for_predict)
                    model_query_ids.append(index - query_offset)
                    result_query_ids.append(index)
                    sent_ids.append(sent_id)

            partial_results.append(partial_result)
        return texts, model_query_ids, result_query_ids, sent_ids, partial_results