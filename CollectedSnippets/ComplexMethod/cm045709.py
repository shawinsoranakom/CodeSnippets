def __wrapped__(
        self, messages_list: list[list[dict] | pw.Json | str], **kwargs
    ) -> list[str | None]:

        def decode_messages(messages: list[dict] | pw.Json | str) -> list[dict] | str:
            if isinstance(messages, str):
                return messages
            else:
                return _prepare_messages(messages)

        messages_decoded_list = [
            decode_messages(messages) for messages in messages_list
        ]
        kwargs = _extract_value_inside_dict(kwargs)
        constant_kwargs = {}
        per_row_kwargs = {}

        if kwargs:
            for key, values in kwargs.items():
                v = values[0]
                if all(value == v for value in values):
                    constant_kwargs[key] = v
                else:
                    per_row_kwargs[key] = values

        def decode_output(output) -> str | None:
            result = output[0]["generated_text"]
            if isinstance(result, list):
                return result[-1]["content"]
            else:
                return result

        # if kwargs are not the same for every message we cannot batch them
        # huggingface does not allow batching if tokenizer or tokenizer.pad_token_id is None
        if (
            per_row_kwargs
            or self.pipeline.tokenizer is None
            or self.pipeline.tokenizer.pad_token_id is None
        ):

            def infer_single(messages, kwargs) -> str | None:
                kwargs = {**self.kwargs, **constant_kwargs, **kwargs}
                output = self.pipeline(messages, **kwargs)
                return decode_output(output)

            list_of_per_row_kwargs = [
                dict(zip(per_row_kwargs, values))
                for values in zip(*per_row_kwargs.values())
            ]

            if list_of_per_row_kwargs:
                result_list = [
                    infer_single(messages, kwargs)
                    for messages, kwargs in zip(
                        messages_decoded_list, list_of_per_row_kwargs
                    )
                ]
            else:
                result_list = [
                    infer_single(messages, {}) for messages in messages_decoded_list
                ]

            return result_list

        else:
            kwargs = {**self.kwargs, **constant_kwargs}
            output_list = self.pipeline(messages_decoded_list, **kwargs)

            if output_list is None:
                return [None] * len(messages_list)

            result_list = [decode_output(output) for output in output_list]
            return result_list