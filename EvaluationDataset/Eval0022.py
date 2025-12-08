def remove_duplicates(key: str) -> str:

    key_no_dups = ""
    for ch in key:
        if ch == " " or (ch not in key_no_dups and ch.isalpha()):
            key_no_dups += ch
    return key_no_dups
