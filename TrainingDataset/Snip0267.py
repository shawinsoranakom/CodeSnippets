def main() -> None:
    message = "HELLO WORLD"
    encrypted_message, key = encrypt(message)

    decrypted_message = decrypt(encrypted_message, key)
    print(f"Decrypted message: {decrypted_message}")
