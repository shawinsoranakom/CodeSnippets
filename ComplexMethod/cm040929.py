def generate_secret_value(
        self,
        length: int,
        excl_lower: bool,
        excl_upper: bool,
        excl_chars: str,
        excl_numbers: bool,
        excl_punct: bool,
        incl_spaces: bool,
        req_each: bool,
    ) -> str:
        """WARN: This is NOT a secure way to generate secrets - use only for testing and not in production use cases!"""

        # TODO: add a couple of unit tests for this function ...

        punctuation = r"!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"
        alphabet = ""
        if not excl_punct:
            alphabet += punctuation
        if not excl_upper:
            alphabet += string.ascii_uppercase
        if not excl_lower:
            alphabet += string.ascii_lowercase
        if not excl_numbers:
            alphabet += "".join([str(i) for i in list(range(10))])
        if incl_spaces:
            alphabet += " "
        if req_each:
            LOG.info("Secret generation option 'RequireEachIncludedType' not yet supported")

        for char in excl_chars:
            alphabet = alphabet.replace(char, "")

        result = [alphabet[random.randrange(len(alphabet))] for _ in range(length)]
        result = "".join(result)
        return result