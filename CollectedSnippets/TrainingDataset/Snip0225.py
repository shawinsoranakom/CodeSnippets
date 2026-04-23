def generate_key(message: str, key: str) -> str:
    
    x = len(message)
    i = 0
    while True:
        if x == i:
            i = 0
        if len(key) == len(message):
            break
        key += key[i]
        i += 1
    return key
