def _forward(self, model_inputs, return_timestamps=False, **generate_kwargs):
        attention_mask = model_inputs.pop("attention_mask", None)
        stride = model_inputs.pop("stride", None)
        num_frames = model_inputs.pop("num_frames", None)
        is_last = model_inputs.pop("is_last")

        if stride is not None and num_frames is not None:
            raise ValueError("num_frames must be used only when stride is None")

        if self.type in {"seq2seq", "seq2seq_whisper"}:
            # Consume values so we can let extra information flow freely through
            # the pipeline (important for `partial` in microphone)
            if "input_features" in model_inputs:
                inputs = model_inputs.pop("input_features")
            elif "input_values" in model_inputs:
                inputs = model_inputs.pop("input_values")
            else:
                raise ValueError(
                    "Seq2Seq speech recognition model requires either a "
                    f"`input_features` or `input_values` key, but only has {model_inputs.keys()}"
                )

            # custom processing for Whisper timestamps and word-level timestamps
            return_timestamps = return_timestamps or getattr(self.generation_config, "return_timestamps", False)
            if return_timestamps and self.type == "seq2seq_whisper":
                generate_kwargs["return_timestamps"] = bool(return_timestamps)
                if return_timestamps == "word":
                    generate_kwargs["return_token_timestamps"] = True
                    generate_kwargs["return_segments"] = True

            # User-defined `generation_config` passed to the pipeline call take precedence
            if "generation_config" not in generate_kwargs:
                generate_kwargs["generation_config"] = self.generation_config

            main_input_name = self.model.main_input_name if hasattr(self.model, "main_input_name") else "inputs"
            generate_kwargs = {
                main_input_name: inputs,
                "attention_mask": attention_mask,
                **generate_kwargs,
            }
            tokens = self.model.generate(**generate_kwargs)

            # whisper longform generation stores timestamps in "segments"
            if return_timestamps == "word" and self.type == "seq2seq_whisper":
                if "segments" not in tokens:
                    out = {"tokens": tokens["sequences"], "token_timestamps": tokens["token_timestamps"]}
                else:
                    token_timestamps = [
                        torch.cat([segment["token_timestamps"] for segment in segment_list])
                        for segment_list in tokens["segments"]
                    ]
                    out = {"tokens": tokens["sequences"], "token_timestamps": token_timestamps}
            else:
                out = {"tokens": tokens}
            if self.type == "seq2seq_whisper":
                if stride is not None:
                    out["stride"] = stride

        else:
            inputs = {
                self.model.main_input_name: model_inputs.pop(self.model.main_input_name),
                "attention_mask": attention_mask,
            }
            outputs = self.model(**inputs)
            logits = outputs.logits

            if self.type == "ctc_with_lm":
                out = {"logits": logits}
            else:
                out = {"tokens": logits.argmax(dim=-1)}
            if stride is not None:
                # Send stride to `postprocess`.
                # it needs to be handled there where
                # the pieces are to be concatenated.
                ratio = 1 / self._align_to
                if isinstance(stride, tuple):
                    out["stride"] = rescale_stride([stride], ratio)[0]
                else:
                    out["stride"] = rescale_stride(stride, ratio)
        # Leftover
        extra = model_inputs
        return {"is_last": is_last, **out, **extra}