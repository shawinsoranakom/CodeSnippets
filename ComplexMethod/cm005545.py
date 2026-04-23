def _get_assistant_to_target_input_ids(self):
        target_vocab = self._target_tokenizer.get_vocab()
        assistant_vocab = self._assistant_tokenizer.get_vocab()

        space_str = " "
        target_space_ids = self._target_tokenizer(space_str, add_special_tokens=False)["input_ids"]
        if len(target_space_ids) > 0:
            target_space_sign = self._target_tokenizer.convert_ids_to_tokens(target_space_ids)[0][0]

            assistant_space_ids = self._assistant_tokenizer(space_str, add_special_tokens=False)["input_ids"]
            if len(assistant_space_ids) > 0:
                assistant_space_sign = self._assistant_tokenizer.convert_ids_to_tokens(assistant_space_ids)[0][0]

                if target_space_sign != assistant_space_sign:
                    # If the assistant tokenizer has a different space sign than the target tokenizer,
                    # we need to replace the assistant space sign with the target space sign in the assistant_vocab.
                    assistant_vocab = {
                        (
                            tok.replace(assistant_space_sign, target_space_sign, 1)
                            if tok.startswith(assistant_space_sign)
                            else tok
                        ): idx
                        for tok, idx in assistant_vocab.items()
                    }

        max_assistant_index = max(assistant_vocab.values())
        assistant_to_target_input_ids = torch.full((max_assistant_index + 1,), self.SUPPRESS_TOKEN_ID, dtype=int)
        target_to_assistant_input_ids: dict[int, int] = {}
        for tok, assistant_id in assistant_vocab.items():
            target_id = target_vocab.get(tok)
            if target_id is not None:
                assistant_to_target_input_ids[assistant_id] = target_id
                target_to_assistant_input_ids[target_id] = assistant_id
        return assistant_to_target_input_ids.to(self._assistant_model_device), target_to_assistant_input_ids