def _preprocess(self, inputs):
        with tf.device("CPU:0"):
            inputs = tf_utils.ensure_tensor(inputs, dtype=tf.string)
            if self._standardize in ("lower", "lower_and_strip_punctuation"):
                inputs = tf.strings.lower(inputs)
            if self._standardize in (
                "strip_punctuation",
                "lower_and_strip_punctuation",
            ):
                inputs = tf.strings.regex_replace(
                    inputs, r'[!"#$%&()\*\+,-\./:;<=>?@\[\\\]^_`{|}~\']', ""
                )
            if callable(self._standardize):
                inputs = self._standardize(inputs)

            if self._split is not None:
                # If we are splitting, we validate that the 1st axis is of
                # dimension 1 and so can be squeezed out. We do this here
                # instead of after splitting for performance reasons - it's
                # more expensive to squeeze a ragged tensor.
                if inputs.shape.rank > 1:
                    if inputs.shape[-1] != 1:
                        raise ValueError(
                            "When using `TextVectorization` to tokenize "
                            "strings, the input rank must be 1 or the last "
                            f"shape dimension must be 1. Received: "
                            f"inputs.shape={inputs.shape} with "
                            f"rank={inputs.shape.rank}"
                        )
                    else:
                        inputs = tf.squeeze(inputs, axis=-1)
                if self._split == "whitespace":
                    # This treats multiple whitespaces as one whitespace,
                    # and strips leading and trailing whitespace.
                    inputs = tf.strings.split(inputs)
                elif self._split == "character":
                    inputs = tf.strings.unicode_split(inputs, "UTF-8")
                elif callable(self._split):
                    inputs = self._split(inputs)

            # Note that 'inputs' here can be either ragged or dense depending
            # on the configuration choices for this Layer. The strings.ngrams
            # op, however, does support both ragged and dense inputs.
            if self._ngrams is not None:
                inputs = tf.strings.ngrams(
                    inputs, ngram_width=self._ngrams, separator=" "
                )
            return inputs