def __post_init__(self):
        if self.mlm:
            if self.tokenizer.mask_token is None:
                raise ValueError(
                    "This tokenizer does not have a mask token which is necessary for masked language modeling. "
                    "You should pass `mlm=False` to train on causal language modeling instead."
                )
            if self.mlm_probability is None or self.mlm_probability < 0 or self.mlm_probability > 1:
                raise ValueError("mlm_probability should be between 0 and 1.")
            self.mlm_probability = float(self.mlm_probability)
        elif self.whole_word_mask:
            raise ValueError(
                "Whole word masking can only be used with mlm=True."
                "If you want to use whole word masking, please set mlm=True."
            )
        if self.mask_replace_prob + self.random_replace_prob > 1:
            raise ValueError("The sum of mask_replace_prob and random_replace_prob should not exceed 1")
        if self.mask_replace_prob < 0 or self.mask_replace_prob > 1:
            raise ValueError("mask_replace_prob should be between 0 and 1.")
        if self.random_replace_prob < 0 or self.random_replace_prob > 1:
            raise ValueError("random_replace_prob should be between 0 and 1.")

        if self.whole_word_mask:
            if not self.tokenizer.is_fast:
                warnings.warn(
                    "Whole word masking depends on offset mapping which is only natively available with fast tokenizers.",
                    UserWarning,
                )

            if self.mask_replace_prob < 1:
                warnings.warn(
                    "Random token replacement is not supported with whole word masking. "
                    "Setting mask_replace_prob to 1.",
                )
                self.mask_replace_prob = 1
                self.random_replace_prob = 0

        self.mask_replace_prob = float(self.mask_replace_prob)
        self.random_replace_prob = float(self.random_replace_prob)

        self.generator = None