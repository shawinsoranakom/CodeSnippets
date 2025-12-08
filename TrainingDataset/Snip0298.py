def make_key_files(name: str, key_size: int) -> None:
    if os.path.exists(f"{name}_pubkey.txt") or os.path.exists(f"{name}_privkey.txt"):
        print("\nWARNING:")
        print(
            f'"{name}_pubkey.txt" or "{name}_privkey.txt" already exists. \n'
            "Use a different name or delete these files and re-run this program."
        )
        sys.exit()

    public_key, private_key = generate_key(key_size)
    print(f"\nWriting public key to file {name}_pubkey.txt...")
    with open(f"{name}_pubkey.txt", "w") as out_file:
        out_file.write(f"{key_size},{public_key[0]},{public_key[1]}")

    print(f"Writing private key to file {name}_privkey.txt...")
    with open(f"{name}_privkey.txt", "w") as out_file:
        out_file.write(f"{key_size},{private_key[0]},{private_key[1]}")
