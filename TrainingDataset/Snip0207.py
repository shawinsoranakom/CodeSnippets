def main() -> None:
 
    message = input("Enter message: ").strip()
    key = int(input("Enter key [2000 - 9000]: ").strip())
    mode = input("Encrypt/Decrypt [E/D]: ").strip().lower()

    if mode.startswith("e"):
        mode = "encrypt"
        translated = encrypt_message(key, message)
    elif mode.startswith("d"):
        mode = "decrypt"
        translated = decrypt_message(key, message)
    print(f"\n{mode.title()}ed text: \n{translated}")
