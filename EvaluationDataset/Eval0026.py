def main() -> None:
    message = input("Enter message to encode or decode: ").strip()
    key = input("Enter keyword: ").strip()
    option = input("Encipher or decipher? E/D:").strip()[0].lower()
    try:
        func = {"e": encipher, "d": decipher}[option]
    except KeyError:
        raise KeyError("invalid input option")
    cipher_map = create_cipher_map(key)
    print(func(message, cipher_map))
