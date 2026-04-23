def main() -> None:
    message = input("Enter message: ")
    key = "LFWOAYUISVKMNXPBDCRJTQEGHZ"
    resp = input("Encrypt/Decrypt [e/d]: ")

    check_valid_key(key)

    if resp.lower().startswith("e"):
        mode = "encrypt"
        translated = encrypt_message(key, message)
    elif resp.lower().startswith("d"):
        mode = "decrypt"
        translated = decrypt_message(key, message)

    print(f"\n{mode.title()}ion: \n{translated}")
