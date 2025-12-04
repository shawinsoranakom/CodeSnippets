def atbash_slow(sequence: str) -> str:
 
    output = ""
    for i in sequence:
        extract = ord(i)
        if 65 <= extract <= 90:
            output += chr(155 - extract)
        elif 97 <= extract <= 122:
            output += chr(219 - extract)
        else:
            output += i
    return output
