def _warn_for_unused_params(self):
        if self.tokenizer is not None and self.token_pattern is not None:
            warnings.warn(
                "The parameter 'token_pattern' will not be used"
                " since 'tokenizer' is not None'"
            )

        if self.preprocessor is not None and callable(self.analyzer):
            warnings.warn(
                "The parameter 'preprocessor' will not be used"
                " since 'analyzer' is callable'"
            )

        if (
            self.ngram_range != (1, 1)
            and self.ngram_range is not None
            and callable(self.analyzer)
        ):
            warnings.warn(
                "The parameter 'ngram_range' will not be used"
                " since 'analyzer' is callable'"
            )
        if self.analyzer != "word" or callable(self.analyzer):
            if self.stop_words is not None:
                warnings.warn(
                    "The parameter 'stop_words' will not be used"
                    " since 'analyzer' != 'word'"
                )
            if (
                self.token_pattern is not None
                and self.token_pattern != r"(?u)\b\w\w+\b"
            ):
                warnings.warn(
                    "The parameter 'token_pattern' will not be used"
                    " since 'analyzer' != 'word'"
                )
            if self.tokenizer is not None:
                warnings.warn(
                    "The parameter 'tokenizer' will not be used"
                    " since 'analyzer' != 'word'"
                )