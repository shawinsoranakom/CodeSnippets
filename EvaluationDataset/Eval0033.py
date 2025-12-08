def main() -> None:
    message = input("Enter message: ")
    key = int(input(f"Enter key [2-{len(message) - 1}]: "))
    mode = input("Encryption/Decryption [e/d]: ")

    if mode.lower().startswith("e"):
        text = encrypt_message(key, message)
    elif mode.lower().startswith("d"):
        text = decrypt_message(key, message)

    print(f"Output:\n{text + '|'}")
