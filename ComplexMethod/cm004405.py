def pad(
        self,
        encoded_inputs: BatchEncoding
        | list[BatchEncoding]
        | dict[str, EncodedInput]
        | dict[str, list[EncodedInput]]
        | list[dict[str, EncodedInput]],
        padding: bool | str | PaddingStrategy = True,
        max_length: int | None = None,
        max_entity_length: int | None = None,
        pad_to_multiple_of: int | None = None,
        padding_side: str | None = None,
        return_attention_mask: bool | None = None,
        return_tensors: str | TensorType | None = None,
        verbose: bool = True,
    ) -> BatchEncoding:
        """
        Pad a single encoded input or a batch of encoded inputs up to predefined length or to the max sequence length
        in the batch. Padding side (left/right) padding token ids are defined at the tokenizer level (with
        `self.padding_side`, `self.pad_token_id` and `self.pad_token_type_id`) .. note:: If the `encoded_inputs` passed
        are dictionary of numpy arrays or PyTorch tensors  the result will use the same type unless
        you provide a different tensor type with `return_tensors`. In the case of PyTorch tensors, you will lose the
        specific device of your tensors however.

        Args:
            encoded_inputs ([`BatchEncoding`], list of [`BatchEncoding`], `dict[str, list[int]]`, `dict[str, list[list[int]]` or `list[dict[str, list[int]]]`):
                Tokenized inputs. Can represent one input ([`BatchEncoding`] or `dict[str, list[int]]`) or a batch of
                tokenized inputs (list of [`BatchEncoding`], *dict[str, list[list[int]]]* or *list[dict[str,
                list[int]]]*) so you can use this method during preprocessing as well as in a PyTorch Dataloader
                collate function. Instead of `list[int]` you can have tensors (numpy arrays, or PyTorch tensors),
                see the note above for the return type.
            padding (`bool`, `str` or [`~utils.PaddingStrategy`], *optional*, defaults to `True`):
                 Select a strategy to pad the returned sequences (according to the model's padding side and padding
                 index) among:

                - `True` or `'longest'`: Pad to the longest sequence in the batch (or no padding if only a single
                  sequence if provided).
                - `'max_length'`: Pad to a maximum length specified with the argument `max_length` or to the maximum
                  acceptable input length for the model if that argument is not provided.
                - `False` or `'do_not_pad'` (default): No padding (i.e., can output a batch with sequences of different
                  lengths).
            max_length (`int`, *optional*):
                Maximum length of the returned list and optionally padding length (see above).
            max_entity_length (`int`, *optional*):
                The maximum length of the entity sequence.
            pad_to_multiple_of (`int`, *optional*):
                If set will pad the sequence to a multiple of the provided value. This is especially useful to enable
                the use of Tensor Cores on NVIDIA hardware with compute capability `>= 7.5` (Volta).
            padding_side:
                The side on which the model should have padding applied. Should be selected between ['right', 'left'].
                Default value is picked from the class attribute of the same name.
            return_attention_mask (`bool`, *optional*):
                Whether to return the attention mask. If left to the default, will return the attention mask according
                to the specific tokenizer's default, defined by the `return_outputs` attribute. [What are attention
                masks?](../glossary#attention-mask)
            return_tensors (`str` or [`~utils.TensorType`], *optional*):
                If set, will return tensors instead of list of python integers. Acceptable values are:

                - `'pt'`: Return PyTorch `torch.Tensor` objects.
                - `'np'`: Return Numpy `np.ndarray` objects.
            verbose (`bool`, *optional*, defaults to `True`):
                Whether or not to print more information and warnings.
        """
        # If we have a list of dicts, let's convert it in a dict of lists
        # We do this to allow using this method as a collate_fn function in PyTorch Dataloader
        if isinstance(encoded_inputs, (list, tuple)) and isinstance(encoded_inputs[0], Mapping):
            # Call .keys() explicitly for compatibility with TensorDict and other Mapping subclasses
            encoded_inputs = {key: [example[key] for example in encoded_inputs] for key in encoded_inputs[0].keys()}

        # The model's main input name, usually `input_ids`, has be passed for padding
        if self.model_input_names[0] not in encoded_inputs:
            raise ValueError(
                "You should supply an encoding or a list of encodings to this method "
                f"that includes {self.model_input_names[0]}, but you provided {list(encoded_inputs.keys())}"
            )

        required_input = encoded_inputs[self.model_input_names[0]]

        if not required_input:
            if return_attention_mask:
                encoded_inputs["attention_mask"] = []
            return encoded_inputs

        # If we have PyTorch/NumPy tensors/arrays as inputs, we cast them as python objects
        # and rebuild them afterwards if no return_tensors is specified
        # Note that we lose the specific device the tensor may be on for PyTorch

        first_element = required_input[0]
        if isinstance(first_element, (list, tuple)):
            # first_element might be an empty list/tuple in some edge cases so we grab the first non empty element.
            index = 0
            while len(required_input[index]) == 0:
                index += 1
            if index < len(required_input):
                first_element = required_input[index][0]
        # At this state, if `first_element` is still a list/tuple, it's an empty one so there is nothing to do.
        if not isinstance(first_element, (int, list, tuple)):
            if is_torch_tensor(first_element):
                return_tensors = "pt" if return_tensors is None else return_tensors
            elif isinstance(first_element, np.ndarray):
                return_tensors = "np" if return_tensors is None else return_tensors
            else:
                raise ValueError(
                    f"type of {first_element} unknown: {type(first_element)}. "
                    "Should be one of a python, numpy, or pytorch object."
                )

            for key, value in encoded_inputs.items():
                encoded_inputs[key] = to_py_obj(value)

        # Convert padding_strategy in PaddingStrategy
        padding_strategy, _, max_length, _ = self._get_padding_truncation_strategies(
            padding=padding, max_length=max_length, verbose=verbose
        )

        if max_entity_length is None:
            max_entity_length = self.max_entity_length

        required_input = encoded_inputs[self.model_input_names[0]]
        if required_input and not isinstance(required_input[0], (list, tuple)):
            encoded_inputs = self._pad(
                encoded_inputs,
                max_length=max_length,
                max_entity_length=max_entity_length,
                padding_strategy=padding_strategy,
                pad_to_multiple_of=pad_to_multiple_of,
                padding_side=padding_side,
                return_attention_mask=return_attention_mask,
            )
            return BatchEncoding(encoded_inputs, tensor_type=return_tensors)

        batch_size = len(required_input)
        if any(len(v) != batch_size for v in encoded_inputs.values()):
            raise ValueError("Some items in the output dictionary have a different batch size than others.")

        if padding_strategy == PaddingStrategy.LONGEST:
            max_length = max(len(inputs) for inputs in required_input)
            max_entity_length = (
                max(len(inputs) for inputs in encoded_inputs["entity_ids"]) if "entity_ids" in encoded_inputs else 0
            )
            padding_strategy = PaddingStrategy.MAX_LENGTH

        batch_outputs = {}
        for i in range(batch_size):
            inputs = {k: v[i] for k, v in encoded_inputs.items()}
            outputs = self._pad(
                inputs,
                max_length=max_length,
                max_entity_length=max_entity_length,
                padding_strategy=padding_strategy,
                pad_to_multiple_of=pad_to_multiple_of,
                padding_side=padding_side,
                return_attention_mask=return_attention_mask,
            )

            for key, value in outputs.items():
                if key not in batch_outputs:
                    batch_outputs[key] = []
                batch_outputs[key].append(value)

        return BatchEncoding(batch_outputs, tensor_type=return_tensors)