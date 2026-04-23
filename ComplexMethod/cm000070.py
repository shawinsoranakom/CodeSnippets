def find_secret_passcode(logins: list[str]) -> int:
    """
    Returns the shortest possible secret passcode of unknown length.

    >>> find_secret_passcode(["135", "259", "235", "189", "690", "168", "120",
    ...     "136", "289", "589", "160", "165", "580", "369", "250", "280"])
    12365890

    >>> find_secret_passcode(["426", "281", "061", "819" "268", "406", "420",
    ...     "428", "209", "689", "019", "421", "469", "261", "681", "201"])
    4206819
    """

    # Split each login by character e.g. '319' -> ('3', '1', '9')
    split_logins = [tuple(login) for login in logins]

    unique_chars = {char for login in split_logins for char in login}

    for permutation in itertools.permutations(unique_chars):
        satisfied = True
        for login in logins:
            if not (
                permutation.index(login[0])
                < permutation.index(login[1])
                < permutation.index(login[2])
            ):
                satisfied = False
                break

        if satisfied:
            return int("".join(permutation))

    raise Exception("Unable to find the secret passcode")