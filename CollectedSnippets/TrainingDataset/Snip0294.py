def main() -> None:
    filename = "encrypted_file.txt"
    response = input(r"Encrypt\Decrypt [e\d]: ")

    if response.lower().startswith("e"):
        mode = "encrypt"
    elif response.lower().startswith("d"):
        mode = "decrypt"

    if mode == "encrypt":
        if not os.path.exists("rsa_pubkey.txt"):
            rkg.make_key_files("rsa", 1024)

        message = input("\nEnter message: ")
        pubkey_filename = "rsa_pubkey.txt"
        print(f"Encrypting and writing to {filename}...")
        encrypted_text = encrypt_and_write_to_file(filename, pubkey_filename, message)

        print("\nEncrypted text:")
        print(encrypted_text)

    elif mode == "decrypt":
        privkey_filename = "rsa_privkey.txt"
        print(f"Reading from {filename} and decrypting...")
        decrypted_text = read_from_file_and_decrypt(filename, privkey_filename)
        print("writing decryption to rsa_decryption.txt...")
        with open("rsa_decryption.txt", "w") as dec:
            dec.write(decrypted_text)

        print("\nDecryption:")
        print(decrypted_text)

