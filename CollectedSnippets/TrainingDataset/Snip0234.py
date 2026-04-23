def brute_force(input_string: str, alphabet: str | None = None) -> dict[int, str]:
   
    alpha = alphabet or ascii_letters

    brute_force_data = {}

    for key in range(1, len(alpha) + 1):
        brute_force_data[key] = decrypt(input_string, key, alpha)

    return brute_force_data
