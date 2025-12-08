def main() -> None:
    message = input("Enter message: ")
    key = input("Enter key [alphanumeric]: ")
    mode = input("Encrypt/Decrypt [e/d]: ")

    if mode.lower().startswith("e"):
        mode = "encrypt"
        translated = encrypt_message(key, message)
    elif mode.lower().startswith("d"):
        mode = "decrypt"
        translated = decrypt_message(key, message)

    print(f"\n{mode.title()}ed message:")
    print(translated)
