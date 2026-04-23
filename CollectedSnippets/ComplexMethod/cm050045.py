def check_vat_ve(self, vat):
        # https://tin-check.com/en/venezuela/
        # https://techdocs.broadcom.com/us/en/symantec-security-software/information-security/data-loss-prevention/15-7/About-content-packs/What-s-included-in-Content-Pack-2021-02/Updated-data-identifiers-in-Content-Pack-2021-02/venezuela-national-identification-number-v115451096-d327e108002-CP2021-02.html
        # Sources last visited on 2022-12-09

        # VAT format: (kind - 1 letter)(identifier number - 8-digit number)(check digit - 1 digit)
        vat_regex = re.compile(r"""
            ([vecjpg])                          # group 1 - kind
            (
                (?P<optional_1>-)?                      # optional '-' (1)
                [0-9]{2}
                (?(optional_1)(?P<optional_2>[.])?)     # optional '.' (2) only if (1)
                [0-9]{3}
                (?(optional_2)[.])                      # mandatory '.' if (2)
                [0-9]{3}
                (?(optional_1)-)                        # mandatory '-' if (1)
            )                                   # group 2 - identifier number
            ([0-9]{1})                          # group X - check digit
        """, re.VERBOSE | re.IGNORECASE)

        matches = re.fullmatch(vat_regex, vat)
        if not matches:
            return False

        kind, identifier_number, *_, check_digit = matches.groups()
        kind = kind.lower()
        identifier_number = identifier_number.replace("-", "").replace(".", "")
        check_digit = int(check_digit)

        if kind == 'v':                   # Venezuela citizenship
            kind_digit = 1
        elif kind == 'e':                 # Foreigner
            kind_digit = 2
        elif kind == 'c' or kind == 'j':  # Township/Communal Council or Legal entity
            kind_digit = 3
        elif kind == 'p':                 # Passport
            kind_digit = 4
        else:                             # Government ('g')
            kind_digit = 5

        # === Checksum validation ===
        multipliers = [3, 2, 7, 6, 5, 4, 3, 2]
        checksum = kind_digit * 4
        checksum += sum(map(lambda n, m: int(n) * m, identifier_number, multipliers))

        checksum_digit = 11 - checksum % 11
        if checksum_digit > 9:
            checksum_digit = 0

        return check_digit == checksum_digit