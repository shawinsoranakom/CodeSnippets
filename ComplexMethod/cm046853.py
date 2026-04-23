def fix_sentencepiece_gguf(saved_location):
    """
    Fixes sentencepiece tokenizers which did not extend the vocabulary with
    user defined tokens.
    Inspiration from https://github.com/ggerganov/llama.cpp/blob/master/convert_hf_to_gguf.py
    """
    from copy import deepcopy
    from transformers.utils import sentencepiece_model_pb2
    import json
    from enum import IntEnum

    class SentencePieceTokenTypes(IntEnum):
        NORMAL = 1
        UNKNOWN = 2
        CONTROL = 3
        USER_DEFINED = 4
        UNUSED = 5
        BYTE = 6

    # Load tokenizer.model
    tokenizer_file = sentencepiece_model_pb2.ModelProto()
    if not os.path.isfile(f"{saved_location}/tokenizer.model"):
        return
    tokenizer_file.ParseFromString(
        open(f"{saved_location}/tokenizer.model", "rb").read()
    )
    sentence_piece_size = len(tokenizer_file.pieces)

    # Load added_tokens_json
    if not os.path.isfile(f"{saved_location}/added_tokens.json"):
        return
    with open(f"{saved_location}/added_tokens.json", "r", encoding = "utf-8") as file:
        added_tokens_json = json.load(file)
    if len(added_tokens_json) == 0:
        return

    added_tokens_json = dict(
        sorted(added_tokens_json.items(), key = lambda item: item[1])
    )
    new_size = sentence_piece_size + len(added_tokens_json)

    # Confirm added_tokens_json is correct
    added_tokens_ids = np.array(list(added_tokens_json.values()))
    diff = np.diff(added_tokens_ids)
    if diff.min() != 1 or diff.max() != 1:
        return
    if added_tokens_ids.min() != sentence_piece_size:
        return

    # Edit sentence piece tokens with added_tokens_json
    logger.warning(
        f"Unsloth: Extending {saved_location}/tokenizer.model with added_tokens.json.\n"
        f"Originally tokenizer.model is of size ({sentence_piece_size}).\n"
        f"But we need to extend to sentencepiece vocab size ({new_size})."
    )
    new_tokens = deepcopy(tokenizer_file.pieces[-len(added_tokens_ids) :])
    for new_token, added_token in zip(new_tokens, added_tokens_json.keys()):
        new_token.piece = added_token.encode("utf-8")
        new_token.score = -1000.0
        new_token.type = SentencePieceTokenTypes.USER_DEFINED

    tokenizer_file.pieces.extend(new_tokens)

    with open(f"{saved_location}/tokenizer.model", "wb") as file:
        file.write(tokenizer_file.SerializeToString())

    # Add padding tokens
    # actual_vocab_size = model.config.vocab_size
    # padding = actual_vocab_size - len(tokenizer_file.pieces)
    return