def split_text(
    text: str,
    max_chunk_length: int,
    tokenizer: ModelTokenizer,
    spacy_model: str = "en_core_web_sm",
    with_overlap: bool = True,
) -> Iterator[tuple[str, int]]:
    """
    Split text into chunks of sentences, with each chunk not exceeding the max length.

    Args:
        text (str): The text to split.
        spacy_model (str): The spaCy model to use for sentence splitting.
        max_chunk_length (int, optional): The maximum length of a chunk.
        tokenizer (ModelTokenizer): Tokenizer to use for determining chunk length.
        with_overlap (bool, optional): Whether to allow overlap between chunks.

    Yields:
        str: The next chunk of text

    Raises:
        ValueError: when a sentence is longer than the maximum length
    """
    text_length = len(tokenizer.encode(text))

    if text_length < max_chunk_length:
        yield text, text_length
        return

    n_chunks = math.ceil(text_length / max_chunk_length)
    target_chunk_length = math.ceil(text_length / n_chunks)

    nlp: spacy.language.Language = spacy.load(spacy_model)
    nlp.add_pipe("sentencizer")
    doc = nlp(text)
    sentences = [sentence.text.strip() for sentence in doc.sents]

    current_chunk: list[str] = []
    current_chunk_length = 0
    last_sentence = None
    last_sentence_length = 0

    i = 0
    while i < len(sentences):
        sentence = sentences[i]
        sentence_length = len(tokenizer.encode(sentence))
        expected_chunk_length = current_chunk_length + 1 + sentence_length

        if (
            expected_chunk_length < max_chunk_length
            # try to create chunks of approximately equal size
            and expected_chunk_length - (sentence_length / 2) < target_chunk_length
        ):
            current_chunk.append(sentence)
            current_chunk_length = expected_chunk_length

        elif sentence_length < max_chunk_length:
            if last_sentence:
                yield " ".join(current_chunk), current_chunk_length
                current_chunk = []
                current_chunk_length = 0

                if with_overlap:
                    overlap_max_length = max_chunk_length - sentence_length - 1
                    if last_sentence_length < overlap_max_length:
                        current_chunk += [last_sentence]
                        current_chunk_length += last_sentence_length + 1
                    elif overlap_max_length > 5:
                        # add as much from the end of the last sentence as fits
                        current_chunk += [
                            list(
                                chunk_content(
                                    content=last_sentence,
                                    max_chunk_length=overlap_max_length,
                                    tokenizer=tokenizer,
                                )
                            ).pop()[0],
                        ]
                        current_chunk_length += overlap_max_length + 1

            current_chunk += [sentence]
            current_chunk_length += sentence_length

        else:  # sentence longer than maximum length -> chop up and try again
            sentences[i : i + 1] = [
                chunk
                for chunk, _ in chunk_content(sentence, target_chunk_length, tokenizer)
            ]
            continue

        i += 1
        last_sentence = sentence
        last_sentence_length = sentence_length

    if current_chunk:
        yield " ".join(current_chunk), current_chunk_length