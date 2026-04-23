def pad(self, *args, **kwargs):
        """
        Collates the audio and text inputs, as well as their targets, into a padded batch.

        Audio inputs are padded by SpeechT5FeatureExtractor's [`~SpeechT5FeatureExtractor.pad`]. Text inputs are padded
        by SpeechT5Tokenizer's [`~SpeechT5Tokenizer.pad`].

        Valid input combinations are:

        - `input_ids` only
        - `input_values` only
        - `labels` only, either log-mel spectrograms or text tokens
        - `input_ids` and log-mel spectrogram `labels`
        - `input_values` and text `labels`

        Please refer to the docstring of the above two methods for more information.
        """
        input_values = kwargs.pop("input_values", None)
        input_ids = kwargs.pop("input_ids", None)
        labels = kwargs.pop("labels", None)

        if input_values is not None and input_ids is not None:
            raise ValueError("Cannot process both `input_values` and `input_ids` inputs.")
        if input_values is None and input_ids is None and labels is None:
            raise ValueError(
                "You need to specify either an `input_values`, `input_ids`, or `labels` input to be padded."
            )

        if input_values is not None:
            inputs = self.feature_extractor.pad(input_values, *args, **kwargs)
        elif input_ids is not None:
            inputs = self.tokenizer.pad(input_ids, **kwargs)
        else:
            inputs = None

        if labels is not None:
            if "input_ids" in labels or (isinstance(labels, list) and "input_ids" in labels[0]):
                targets = self.tokenizer.pad(labels, **kwargs)
                labels = targets["input_ids"]
            else:
                feature_size_hack = self.feature_extractor.feature_size
                self.feature_extractor.feature_size = self.feature_extractor.num_mel_bins
                targets = self.feature_extractor.pad(labels, *args, **kwargs)
                self.feature_extractor.feature_size = feature_size_hack
                labels = targets["input_values"]
        else:
            targets = None

        if inputs is None:
            return targets

        if targets is not None:
            inputs["labels"] = labels

            decoder_attention_mask = targets.get("attention_mask")
            if decoder_attention_mask is not None:
                inputs["decoder_attention_mask"] = decoder_attention_mask

        return inputs