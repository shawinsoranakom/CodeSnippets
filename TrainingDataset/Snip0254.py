def mixed_keyword(
    keyword: str, plaintext: str, verbose: bool = False, alphabet: str = ascii_uppercase
) -> str:
    
    keyword = keyword.upper()
    plaintext = plaintext.upper()
    alphabet_set = set(alphabet)

    
    unique_chars = []
    for char in keyword:
        if char in alphabet_set and char not in unique_chars:
            unique_chars.append(char)
    num_unique_chars_in_keyword = len(unique_chars)

    shifted_alphabet = unique_chars + [
        char for char in alphabet if char not in unique_chars
    ]

    modified_alphabet = [
        shifted_alphabet[k : k + num_unique_chars_in_keyword]
        for k in range(0, 26, num_unique_chars_in_keyword)
    ]

   
    mapping = {}
    letter_index = 0
    for column in range(num_unique_chars_in_keyword):
        for row in modified_alphabet:
            if len(row) <= column:
                break

            mapping[alphabet[letter_index]] = row[column]
            letter_index += 1

    if verbose:
        print(mapping)
    return "".join(mapping.get(char, char) for char in plaintext)
