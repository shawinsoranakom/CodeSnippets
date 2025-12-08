def main() -> None:
    message = "Morse code here!"
    print(message)
    message = encrypt(message)
    print(message)
    message = decrypt(message)
    print(message)
