def postprocess(
        self,
        model_outputs,
        return_type=ReturnType.FULL_TEXT,
        continue_final_message=None,
        skip_special_tokens=None,
        **postprocess_kwargs,
    ):
        input_texts = model_outputs["prompt_text"]
        input_texts = [input_texts] if isinstance(input_texts, (str, Chat)) else input_texts
        generated_sequence = model_outputs["generated_sequence"]
        input_ids = model_outputs["input_ids"]
        if return_type == ReturnType.TENSORS:
            return [
                {"input_text": input_texts[i], "generated_token_ids": generated_sequence[i]}
                for i in range(len(input_texts))
            ]

        # Decode inputs and outputs the same way to remove input text from generated text if present
        skip_special_tokens = skip_special_tokens if skip_special_tokens is not None else True
        if getattr(self.tokenizer, "response_schema", False):
            skip_special_tokens = False
        generated_texts = self.processor.post_process_image_text_to_text(
            generated_sequence, skip_special_tokens=skip_special_tokens, **postprocess_kwargs
        )
        decoded_inputs = self.processor.post_process_image_text_to_text(
            input_ids, skip_special_tokens=skip_special_tokens, **postprocess_kwargs
        )

        # Force consistent behavior for including the input text in the output
        if return_type in {ReturnType.NEW_TEXT, ReturnType.FULL_TEXT}:
            # Remove the input text from the generated text if the generated text starts with the input text
            # (accounting for the possibility of a space between the input and generated text)
            new_generated_texts = []
            for text_generated, decoded_input in zip(generated_texts, decoded_inputs):
                # There can be added characters before the input text, so we need to find the beginning of the input text in the generated text
                index_input_text = text_generated.find(decoded_input)
                # Limit the search to 2 residual characters, like spaces or new lines, to avoid removing a large part of the answer
                if 0 <= index_input_text <= 2:
                    # If the input text is found, we remove it
                    new_generated_texts.append(text_generated[index_input_text + len(decoded_input) :])
                else:
                    new_generated_texts.append(text_generated)
            generated_texts = new_generated_texts
        if return_type == ReturnType.FULL_TEXT:
            full_texts = []
            for prompt_text, generated_text in zip(input_texts, generated_texts):
                if isinstance(prompt_text, str):
                    generated_text = prompt_text + generated_text
                elif isinstance(prompt_text, Chat):
                    if continue_final_message is None:
                        # If the user passes a chat ending in an assistant message, we treat it as a prefill by
                        # default because very few models support multiple separate, consecutive assistant messages
                        continue_final_message = prompt_text.messages[-1]["role"] == "assistant"
                    if continue_final_message:
                        # With assistant prefill, concat onto the end of the last message
                        new_text = dict(prompt_text.messages[-1]["content"][-1].items())
                        new_text["text"] += generated_text
                        generated_text = list(prompt_text.messages)[:-1] + [
                            {
                                "role": prompt_text.messages[-1]["role"],
                                "content": prompt_text.messages[-1]["content"][:-1] + [new_text],
                            }
                        ]
                    else:
                        # When we're not starting from a prefill, the output is a new assistant message
                        if getattr(self.tokenizer, "response_schema", False):
                            assistant_message = self.tokenizer.parse_response(generated_text)
                        else:
                            assistant_message = {"role": "assistant", "content": generated_text}
                        generated_text = list(prompt_text.messages) + [assistant_message]
                full_texts.append(generated_text)
            generated_texts = full_texts

        records = [
            {
                "input_text": input_text.messages if isinstance(input_text, Chat) else input_text,
                "generated_text": generated_text,
            }
            for input_text, generated_text in zip(input_texts, generated_texts)
        ]

        return records