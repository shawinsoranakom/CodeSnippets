def test_new_language_codes(self):
        code1, code2 = "myv_Cyrl", "myv_Latn"
        new_codes = FAIRSEQ_LANGUAGE_CODES + [code1, code2]
        # here I create a tokenizer with the default behaviour
        tok1 = NllbTokenizer.from_pretrained("facebook/nllb-200-distilled-600M")
        # here I enhance the model's vocabulary with two new language codes
        tok2 = NllbTokenizer.from_pretrained("facebook/nllb-200-distilled-600M", additional_special_tokens=new_codes)

        # testing that the new codes can work
        self.assertEqual(len(tok2), len(tok1) + 2)
        tok2.tgt_lang = code1
        tok2.src_lang = code2

        self.assertEqual(tok2("šumbrat!").input_ids[0], tok2.convert_tokens_to_ids(code2))
        with tempfile.TemporaryDirectory() as tempdir:
            # testing that saving and loading the tokenizer preserves the new behaviour
            tok2.save_pretrained(tempdir)
            tok3 = NllbTokenizer.from_pretrained(tempdir)
            self.assertEqual(tok2.get_vocab(), tok3.get_vocab())
            tok3.src_lang = code2
            self.assertEqual(tok3("šumbrat!").input_ids[0], tok3.convert_tokens_to_ids(code2))

            # testing that saving and loading the tokenizer preserves the new behaviour
            tok2.save_pretrained(tempdir)
            # Use the original vocab_file from tok2, or load from saved directory
            vocab_file = tok2.vocab_file if hasattr(tok2, "vocab_file") and tok2.vocab_file else None
            if vocab_file is None or not os.path.exists(vocab_file):
                # Fallback: load from saved directory to get vocab_file
                tok_temp = NllbTokenizer.from_pretrained(tempdir)
                vocab_file = tok_temp.vocab_file if hasattr(tok_temp, "vocab_file") and tok_temp.vocab_file else None
            # Extract vocab and merges from sentencepiece model
            if vocab_file and os.path.exists(vocab_file):
                extractor = SentencePieceExtractor(vocab_file)
                vocab_ids, vocab_scores, merges = extractor.extract()
                tok3 = NllbTokenizer(
                    vocab=vocab_ids, merges=merges, vocab_file=vocab_file, additional_special_tokens=None
                )
                self.assertEqual(len(tok3), 256204)  # legacy
                tok4 = NllbTokenizer(
                    vocab=vocab_ids, merges=merges, vocab_file=vocab_file, additional_special_tokens=[]
                )
                self.assertEqual(len(tok4), 256002)
                tok5 = NllbTokenizer(
                    vocab=vocab_ids, merges=merges, vocab_file=vocab_file, additional_special_tokens=[code1, code2]
                )
                self.assertEqual(len(tok5), 256004)