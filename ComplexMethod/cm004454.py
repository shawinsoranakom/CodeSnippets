def __call__(self, *args, **kwargs):
        audio = kwargs.pop("audio", None)
        text = kwargs.pop("text", None)
        text_target = kwargs.pop("text_target", None)
        audio_target = kwargs.pop("audio_target", None)
        sampling_rate = kwargs.pop("sampling_rate", None)

        if audio is not None and text is not None:
            raise ValueError(
                "Cannot process both `audio` and `text` inputs. Did you mean `audio_target` or `text_target`?"
            )
        if audio_target is not None and text_target is not None:
            raise ValueError(
                "Cannot process both `audio_target` and `text_target` inputs. Did you mean `audio` or `text`?"
            )
        if audio is None and audio_target is None and text is None and text_target is None:
            raise ValueError(
                "You need to specify either an `audio`, `audio_target`, `text`, or `text_target` input to process."
            )

        if audio is not None:
            inputs = self.feature_extractor(audio, *args, sampling_rate=sampling_rate, **kwargs)
        elif text is not None:
            inputs = self.tokenizer(text, **kwargs)
        else:
            inputs = None

        if audio_target is not None:
            targets = self.feature_extractor(audio_target=audio_target, *args, sampling_rate=sampling_rate, **kwargs)
            labels = targets["input_values"]
        elif text_target is not None:
            targets = self.tokenizer(text_target, **kwargs)
            labels = targets["input_ids"]
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