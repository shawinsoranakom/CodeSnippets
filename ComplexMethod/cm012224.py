def match_einsum_strings(s: str) -> bool:
    """
    This function takes a string s as input, where s is in the format "3 letter string,
    4 letter string -> 3 letter string".
    It checks if the strings match the rule and returns True if they do, False otherwise.

    The rule is:
    - The three strings have the same first two characters.
    - The first two strings have the same third character.
    - The second and third strings have the same last character.
    """

    # Split the input string into parts
    parts = s.replace("->", ",").split(",")

    # Strip leading/trailing whitespaces from each part
    parts = [part.strip() for part in parts]

    # Check if we have exactly three parts
    if len(parts) != 3:
        return False

    # Extract the strings
    s1, s2, s3 = parts

    # Check if the strings have the correct lengths
    if len(s1) != 3 or len(s2) != 4 or len(s3) != 3:
        return False

    # Check the rule
    return s1[:2] == s2[:2] == s3[:2] and s1[2] == s2[2] and s2[3] == s3[2]