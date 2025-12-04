def decode(coded: str) -> str:
   
    if set(coded) - {"A", "B", " "} != set():
        raise Exception("decode() accepts only 'A', 'B' and spaces")
    decoded = ""
    for word in coded.split():
        while len(word) != 0:
            decoded += decode_dict[word[:5]]
            word = word[5:]
        decoded += " "
    return decoded.strip()
