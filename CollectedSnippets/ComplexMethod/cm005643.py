def postprocess(
        self,
        model_outputs,
        return_type=ReturnType.FULL_TEXT,
        clean_up_tokenization_spaces=True,
        continue_final_message=None,
        skip_special_tokens=None,
    ):
        generated_sequence = model_outputs["generated_sequence"][0]
        input_ids = model_outputs["input_ids"]
        prompt_text = model_outputs["prompt_text"]
        generated_sequence = generated_sequence.numpy().tolist()
        records = []
        other_outputs = model_outputs.get("additional_outputs", {})
        split_keys = {}
        if other_outputs:
            for k, v in other_outputs.items():
                if isinstance(v, torch.Tensor) and v.shape[0] == len(generated_sequence):
                    split_keys[k] = v.numpy().tolist()

        skip_special_tokens = skip_special_tokens if skip_special_tokens is not None else True
        if getattr(self.tokenizer, "response_schema", False):
            skip_special_tokens = False
        for idx, sequence in enumerate(generated_sequence):
            if return_type == ReturnType.TENSORS:
                record = {"generated_token_ids": sequence}
            elif return_type in {ReturnType.NEW_TEXT, ReturnType.FULL_TEXT}:
                # Decode text
                text = self.tokenizer.decode(
                    sequence,
                    skip_special_tokens=skip_special_tokens,
                    clean_up_tokenization_spaces=clean_up_tokenization_spaces,
                )

                # Remove PADDING prompt of the sequence if XLNet or Transfo-XL model is used
                if input_ids is None:
                    prompt_length = 0
                else:
                    prompt_length = len(
                        self.tokenizer.decode(
                            input_ids[0],
                            skip_special_tokens=skip_special_tokens,
                            clean_up_tokenization_spaces=clean_up_tokenization_spaces,
                        )
                    )

                all_text = text[prompt_length:]
                if return_type == ReturnType.FULL_TEXT:
                    if isinstance(prompt_text, str):
                        all_text = prompt_text + all_text
                    elif isinstance(prompt_text, Chat):
                        if continue_final_message is None:
                            # If the user passes a chat ending in an assistant message, we treat it as a prefill by
                            # default because very few models support multiple separate, consecutive assistant messages
                            continue_final_message = prompt_text.messages[-1]["role"] == "assistant"
                        if continue_final_message:
                            # With assistant prefill, concat onto the end of the last message
                            all_text = list(prompt_text.messages)[:-1] + [
                                {
                                    "role": prompt_text.messages[-1]["role"],
                                    "content": prompt_text.messages[-1]["content"] + all_text,
                                }
                            ]
                        else:
                            # When we're not starting from a prefill, the output is a new assistant message
                            if getattr(self.tokenizer, "response_schema", False):
                                assistant_message = self.tokenizer.parse_response(all_text)
                            else:
                                # If there's no schema, then we have to assume it's all content
                                assistant_message = {"role": "assistant", "content": all_text}
                            all_text = list(prompt_text.messages) + [assistant_message]
                record = {"generated_text": all_text}
                for key, values in split_keys.items():
                    record[key] = values[idx]
            records.append(record)

        return records