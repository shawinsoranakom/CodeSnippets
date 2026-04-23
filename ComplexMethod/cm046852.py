def fix_sentencepiece_tokenizer(
    old_tokenizer,
    new_tokenizer,
    token_mapping,
    temporary_location = "_unsloth_sentencepiece_temp",
):
    # From https://github.com/google/sentencepiece/issues/121
    # We need to manually edit the sentencepiece tokenizer!
    try:
        from transformers.convert_slow_tokenizer import import_protobuf

        sentencepiece_model_pb2 = import_protobuf()
    except Exception as e:
        try:
            import google.protobuf
            from unsloth_zoo.utils import Version

            protobuf_version = Version(google.protobuf.__version__)
            if protobuf_version > Version("3.20.3"):
                raise RuntimeError(
                    f"Unsloth: Your protobuf version = {protobuf_version} is too new.\n"
                    f"Please downgrade via `pip install --force-reinstall protobuf==3.20.3`"
                )
        except:
            # This will only work for older SentencePiece versions <= 3.20.3
            from transformers.utils import sentencepiece_model_pb2

    if not os.path.exists(temporary_location):
        os.makedirs(temporary_location)

    # Check if tokenizer.model exists
    if not os.path.isfile(f"{temporary_location}/tokenizer.model"):
        return new_tokenizer

    # First save the old tokenizer
    old_tokenizer.save_pretrained(temporary_location)

    tokenizer_file = sentencepiece_model_pb2.ModelProto()
    tokenizer_file.ParseFromString(
        open(f"{temporary_location}/tokenizer.model", "rb").read()
    )

    # Now save the new tokenizer
    new_tokenizer.save_pretrained(temporary_location)

    # Now correct the old tokenizer's .model file
    for old_token, new_token in token_mapping.items():
        ids = old_tokenizer([old_token], add_special_tokens = False).input_ids
        ids = ids[0]
        if len(ids) != 1:
            # Skip this token!
            print(
                f"Skip mapping {old_token} to {new_token} since {new_token} is already in the tokenizer!"
            )
            continue
        ids = ids[0]
        # [TODO] Hack for Starling - try except
        try:
            tokenizer_piece = tokenizer_file.pieces[ids]
        except:
            continue
        assert tokenizer_piece.piece == old_token
        tokenizer_piece.piece = new_token

    # And now write it
    with open(f"{temporary_location}/tokenizer.model", "wb") as file:
        file.write(tokenizer_file.SerializeToString())

    # And load it!
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        temporary_location,
        eos_token = new_tokenizer.eos_token,
        pad_token = new_tokenizer.pad_token,
    )
    return tokenizer