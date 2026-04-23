def test_tokenizer(slow: PreTrainedTokenizerBase, fast: PreTrainedTokenizerBase) -> None:
    global batch_total
    for i in range(len(dataset)):
        # premise, all languages
        for text in dataset[i]["premise"].values():
            test_string(slow, fast, text)

        # hypothesis, all languages
        for text in dataset[i]["hypothesis"]["translation"]:
            test_string(slow, fast, text)
