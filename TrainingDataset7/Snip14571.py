def paragraph():
    """
    Return a randomly generated paragraph of lorem ipsum text.

    The paragraph consists of between 1 and 4 sentences, inclusive.
    """
    return " ".join(sentence() for i in range(random.randint(1, 4)))