def encrypt(key: str, words: str) -> str:
    cipher = ""
    count = 0
    table = generate_table(key)
    for char in words.upper():
        cipher += get_opponent(table[count], char)
        count = (count + 1) % len(table)
    return cipher
