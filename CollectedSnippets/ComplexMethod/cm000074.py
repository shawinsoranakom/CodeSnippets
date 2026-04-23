def solution(chain_length: int = 60, number_limit: int = 1000000) -> int:
    """
    Returns the number of numbers below number_limit that produce chains with exactly
    chain_length non repeating elements.

    >>> solution(10.0, 1000)
    Traceback (most recent call last):
        ...
    TypeError: Parameters chain_length and number_limit must be int

    >>> solution(10, 1000.0)
    Traceback (most recent call last):
        ...
    TypeError: Parameters chain_length and number_limit must be int

    >>> solution(0, 1000)
    Traceback (most recent call last):
        ...
    ValueError: Parameters chain_length and number_limit must be greater than 0

    >>> solution(10, 0)
    Traceback (most recent call last):
        ...
    ValueError: Parameters chain_length and number_limit must be greater than 0

    >>> solution(10, 1000)
    26
    """

    if not isinstance(chain_length, int) or not isinstance(number_limit, int):
        raise TypeError("Parameters chain_length and number_limit must be int")

    if chain_length <= 0 or number_limit <= 0:
        raise ValueError(
            "Parameters chain_length and number_limit must be greater than 0"
        )

    # the counter for the chains with the exact desired length
    chains_counter = 0
    # the cached sizes of the previous chains
    chain_sets_lengths: dict[int, int] = {}

    for start_chain_element in range(1, number_limit):
        # The temporary set will contain the elements of the chain
        chain_set = set()
        chain_set_length = 0

        # Stop computing the chain when you find a cached size, a repeating item or the
        # length is greater then the desired one.
        chain_element = start_chain_element
        while (
            chain_element not in chain_sets_lengths
            and chain_element not in chain_set
            and chain_set_length <= chain_length
        ):
            chain_set.add(chain_element)
            chain_set_length += 1
            chain_element = digit_factorial_sum(chain_element)

        if chain_element in chain_sets_lengths:
            chain_set_length += chain_sets_lengths[chain_element]

        chain_sets_lengths[start_chain_element] = chain_set_length

        # If chain contains the exact amount of elements increase the counter
        if chain_set_length == chain_length:
            chains_counter += 1

    return chains_counter