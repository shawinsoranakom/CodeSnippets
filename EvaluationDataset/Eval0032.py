def get_random_key() -> str:
    key = list(LETTERS)
    random.shuffle(key)
    return "".join(key)
