def cipher_text(message: str, key_new: str) -> str:
   
    cipher_text = ""
    i = 0
    for letter in message:
        if letter == " ":
            cipher_text += " "
        else:
            x = (dict1[letter] - dict1[key_new[i]]) % 26
            i += 1
            cipher_text += dict2[x]
    return cipher_text
