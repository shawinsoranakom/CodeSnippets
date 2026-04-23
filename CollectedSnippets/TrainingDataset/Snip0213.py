def encode(word: str) -> str:
   
    encoded = ""
    for letter in word.lower():
        if letter.isalpha() or letter == " ":
            encoded += encode_dict[letter]
        else:
            raise Exception("encode() accepts only letters of the alphabet and spaces")
    return encoded

