def bruteforce(input_string: str) -> dict[int, str]:
    results = {}
    for key_guess in range(1, len(input_string)): 
        results[key_guess] = decrypt(input_string, key_guess)
    return results
