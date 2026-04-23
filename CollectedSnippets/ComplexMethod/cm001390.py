async def _process_text(
    text: str,
    instruction: str,
    llm_provider: MultiProvider,
    model_name: ModelName,
    spacy_model: str = "en_core_web_sm",
    output_type: type[str | list[str]] = str,
) -> tuple[str, list[tuple[str, str]]] | list[str]:
    """Process text using the OpenAI API for summarization or information extraction

    Params:
        text (str): The text to process.
        instruction (str): Additional instruction for processing.
        llm_provider: LLM provider to use.
        model_name: The name of the llm model to use.
        spacy_model: The spaCy model to use for sentence splitting.
        output_type: `str` for summaries or `list[str]` for piece-wise info extraction.

    Returns:
        For summarization: tuple[str, None | list[(summary, chunk)]]
        For piece-wise information extraction: list[str]
    """
    if not text.strip():
        raise ValueError("No content")

    text_tlength = llm_provider.count_tokens(text, model_name)
    logger.debug(f"Text length: {text_tlength} tokens")

    max_result_tokens = 500
    max_chunk_length = llm_provider.get_token_limit(model_name) - max_result_tokens - 50
    logger.debug(f"Max chunk length: {max_chunk_length} tokens")

    if text_tlength < max_chunk_length:
        prompt = ChatPrompt(
            messages=[
                ChatMessage.system(
                    "The user is going to give you a text enclosed in triple quotes. "
                    f"{instruction}"
                ),
                ChatMessage.user(f'"""{text}"""'),
            ]
        )

        logger.debug(f"PROCESSING:\n{prompt}")

        response = await llm_provider.create_chat_completion(
            model_prompt=prompt.messages,
            model_name=model_name,
            temperature=0.5,
            max_output_tokens=max_result_tokens,
            completion_parser=lambda s: (
                extract_list_from_json(s.content) if output_type is not str else None
            ),
        )

        if isinstance(response.parsed_result, list):
            logger.debug(f"Raw LLM response: {repr(response.response.content)}")
            fmt_result_bullet_list = "\n".join(f"* {r}" for r in response.parsed_result)
            logger.debug(
                f"\n{'-'*11} EXTRACTION RESULT {'-'*12}\n"
                f"{fmt_result_bullet_list}\n"
                f"{'-'*42}\n"
            )
            return response.parsed_result
        else:
            summary = response.response.content
            logger.debug(f"\n{'-'*16} SUMMARY {'-'*17}\n{summary}\n{'-'*42}\n")
            return summary.strip(), [(summary, text)]
    else:
        chunks = list(
            split_text(
                text,
                max_chunk_length=max_chunk_length,
                tokenizer=llm_provider.get_tokenizer(model_name),
                spacy_model=spacy_model,
            )
        )

        processed_results = []
        for i, (chunk, _) in enumerate(chunks):
            logger.info(f"Processing chunk {i + 1} / {len(chunks)}")
            chunk_result = await _process_text(
                text=chunk,
                instruction=instruction,
                output_type=output_type,
                llm_provider=llm_provider,
                model_name=model_name,
                spacy_model=spacy_model,
            )
            processed_results.extend(
                chunk_result if output_type == list[str] else [chunk_result]
            )

        if output_type == list[str]:
            return processed_results
        else:
            summary, _ = await _process_text(
                "\n\n".join([result[0] for result in processed_results]),
                instruction=(
                    "The text consists of multiple partial summaries. "
                    "Combine these partial summaries into one."
                ),
                llm_provider=llm_provider,
                model_name=model_name,
                spacy_model=spacy_model,
            )
            return summary.strip(), [
                (processed_results[i], chunks[i][0]) for i in range(0, len(chunks))
            ]