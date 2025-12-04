def main() -> None:
    message = "THE GERMAN ATTACK"
    key = "SECRET"
    key_new = generate_key(message, key)
    s = cipher_text(message, key_new)
    print(f"Encrypted Text = {s}")
    print(f"Original Text = {original_text(s, key_new)}")
