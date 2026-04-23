def check_valid_key(key: str) -> None:
    key_list = list(key)
    letters_list = list(LETTERS)
    key_list.sort()
    letters_list.sort()

    if key_list != letters_list:
        sys.exit("Error in the key or symbol set.")

