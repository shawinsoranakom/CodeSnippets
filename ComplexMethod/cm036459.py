def test_mistral_reasoning(
    streaming: bool,
    param_dict: dict,
    mistral_tokenizer: MistralTokenizer,
):
    output = param_dict["output"]

    index_think = output.find("[THINK]")
    len_think = len("[THINK]")
    index_end_think = output.find("[/THINK]")
    len_end_think = len("[/THINK]")

    # encode everything to tokens ids
    output_tokens = []
    if index_think != -1:
        output_before_think = output[:index_think]
        output_tokens += mistral_tokenizer.tokenizer.encode(
            output_before_think, False, False
        )
        output_tokens += [mistral_tokenizer.instruct.BEGIN_THINK]

        if index_end_think != -1:
            output_middle = output[index_think + len_think : index_end_think]
            output_after_think = output[index_end_think + len_end_think :]
            output_tokens += mistral_tokenizer.tokenizer.encode(
                output_middle, False, False
            )
            output_tokens += [mistral_tokenizer.instruct.END_THINK]
            output_tokens += mistral_tokenizer.tokenizer.encode(
                output_after_think, False, False
            )
        else:
            output_middle = output[index_think + len_think :]
            output_tokens += mistral_tokenizer.tokenizer.encode(
                output_middle, False, False
            )
    elif index_end_think != -1:
        output_before_think = output[:index_end_think]
        output_after_think = output[index_end_think + len_end_think :]
        output_tokens += mistral_tokenizer.tokenizer.encode(
            output_before_think, False, False
        )
        output_tokens += [mistral_tokenizer.instruct.END_THINK]
        output_tokens += mistral_tokenizer.tokenizer.encode(
            output_after_think, False, False
        )
    else:
        output_tokens += mistral_tokenizer.tokenizer.encode(output, False, False)

    parser: ReasoningParser = ReasoningParserManager.get_reasoning_parser(parser_name)(
        mistral_tokenizer
    )

    reasoning, content = run_reasoning_extraction_mistral(
        parser, output_tokens, streaming=streaming
    )

    assert reasoning == param_dict["reasoning"]
    assert content == param_dict["content"]

    # Test is_reasoning_end
    is_reasoning_end = parser.is_reasoning_end(output_tokens)
    assert is_reasoning_end == param_dict["is_reasoning_end"]

    # Test extract_content
    if param_dict["content"] is not None:
        # Handle the case where there are tokens outputted before Thinking.
        # This should not occur if the model is well trained and prompted.
        if "[THINK]" in param_dict["output"] and not param_dict["output"].startswith(
            "[THINK]"
        ):
            before_content = param_dict["output"].split("[THINK]")[0]
            before_token_ids = mistral_tokenizer.tokenizer.encode(
                before_content, bos=False, eos=False
            )
            left_to_encode = param_dict["content"][len(before_content) :]
        # Normal situation.
        else:
            before_token_ids = []
            left_to_encode = param_dict["content"]

        content_tokens = parser.extract_content_ids(output_tokens)
        expected_token_ids = before_token_ids + mistral_tokenizer.tokenizer.encode(
            left_to_encode, bos=False, eos=False
        )
        assert content_tokens == expected_token_ids
    else:
        content = parser.extract_content_ids(output_tokens)
        assert content == []