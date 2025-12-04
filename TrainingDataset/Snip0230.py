def decrypt(message: str) -> None:
   
    for key in range(len(string.ascii_uppercase)):
        translated = ""
        for symbol in message:
            if symbol in string.ascii_uppercase:
                num = string.ascii_uppercase.find(symbol)
                num = num - key
                if num < 0:
                    num = num + len(string.ascii_uppercase)
                translated = translated + string.ascii_uppercase[num]
            else:
                translated = translated + symbol
        print(f"Decryption using Key #{key}: {translated}")
