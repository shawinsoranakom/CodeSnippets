def is_strong_password(password: str, min_length: int = 8) -> bool:
    """
    This will check whether a given password is strong or not. The password must be at
    least as long as the provided minimum length, and it must contain at least 1
    lowercase letter, 1 uppercase letter, 1 number and 1 special character.

    >>> is_strong_password('Hwea7$2!')
    True
    >>> is_strong_password('Sh0r1')
    False
    >>> is_strong_password('Hello123')
    False
    >>> is_strong_password('Hello1238udfhiaf038fajdvjjf!jaiuFhkqi1')
    True
    >>> is_strong_password('0')
    False
    """

    if len(password) < min_length:
        return False

    upper = any(char in ascii_uppercase for char in password)
    lower = any(char in ascii_lowercase for char in password)
    num = any(char in digits for char in password)
    spec_char = any(char in punctuation for char in password)

    return upper and lower and num and spec_char