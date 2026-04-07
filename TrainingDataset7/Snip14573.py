def words(count, common=True):
    """
    Return a string of `count` lorem ipsum words separated by a single space.

    If `common` is True, then the first 19 words will be the standard
    'lorem ipsum' words. Otherwise, all words will be selected randomly.
    """
    word_list = list(COMMON_WORDS) if common else []
    c = len(word_list)
    if count > c:
        count -= c
        while count > 0:
            c = min(count, len(WORDS))
            count -= c
            word_list += random.sample(WORDS, c)
    else:
        word_list = word_list[:count]
    return " ".join(word_list)