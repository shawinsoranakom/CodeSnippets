def get_extracted_tokenizer(self, reference_tokenizer=None):
        if reference_tokenizer is None:
            reference_tokenizer = self.get_tokenizer()

        try:
            tokenizer_json_path = os.path.join(self.tmpdirname, "tokenizer.json")
            if not os.path.exists(tokenizer_json_path):
                return None

            extractor = TokenizersExtractor(tokenizer_json_path)
            vocab_ids, vocab_scores, merges, added_tokens_decoder = extractor.extract()
            if _type := getattr(self.tokenizer_class, "model", None):
                if _type.__name__ == "BPE" or _type.__name__ == "WordPiece":
                    vocab = vocab_ids
                else:
                    vocab = vocab_scores

            init_kwargs = {
                "vocab": vocab,
                "merges": merges,
                "do_lower_case": False,
                "keep_accents": True,
                "added_tokens_decoder": dict(added_tokens_decoder.items()),
            }

            tags_dict = getattr(reference_tokenizer, "tags_dict", None)
            if tags_dict is None:
                raise ValueError("MarkupLMTokenizer requires a tags_dict for initialization.")
            init_kwargs["tags_dict"] = tags_dict

            if self.from_pretrained_kwargs is not None:
                init_kwargs.update(self.from_pretrained_kwargs)

            return self.tokenizer_class(**init_kwargs)
        except (TypeError, Exception):
            raise