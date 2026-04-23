def __call__(self, sentences: List[str]) -> List[List[str]]:
        if isinstance(sentences, str):
            sentences = [sentences]

        if self.enable_opencc:
            translated_sentences = []
            for sent in sentences:
                translated_sent = self.cc.convert(sent)
                assert len(translated_sent) == len(sent)
                translated_sentences.append(translated_sent)
            sentences = translated_sentences

        texts, model_query_ids, result_query_ids, sent_ids, partial_results = self._prepare_data(sentences=sentences)
        if len(texts) == 0:
            return partial_results

        model_input = prepare_onnx_input(
            tokenizer=self.tokenizer,
            labels=self.labels,
            char2phonemes=self.char2phonemes,
            chars=self.chars,
            texts=texts,
            query_ids=model_query_ids,
            use_mask=self.config.use_mask,
            window_size=None,
            char2id=self.char2id,
            char_phoneme_masks=self.char_phoneme_masks,
        )

        if not model_input:
            return partial_results

        if self.enable_sentence_dedup:
            preds, _confidences = self._predict_with_sentence_dedup(model_input=model_input, texts=texts)
        else:
            preds, _confidences = self._predict(model_input=model_input)

        if self.config.use_char_phoneme:
            preds = [pred.split(" ")[1] for pred in preds]

        results = partial_results
        for sent_id, query_id, pred in zip(sent_ids, result_query_ids, preds):
            results[sent_id][query_id] = self.style_convert_func(pred)

        return results