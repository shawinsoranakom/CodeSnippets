def main() -> None:
    message = "Hello World"
    key = "QWERTYUIOPASDFGHJKLZXCVBNM"
    mode = "decrypt" 

    if mode == "encrypt":
        translated = encrypt_message(key, message)
    elif mode == "decrypt":
        translated = decrypt_message(key, message)
    print(f"Using the key {key}, the {mode}ed message is: {translated}")
