def setUp(self):
        self.valid_tags = (
            "en",  # language
            "mas",  # language
            "sgn-ase",  # language+extlang
            "fr-CA",  # language+region
            "es-419",  # language+region
            "zh-Hans",  # language+script
            "ca-ES-valencia",  # language+region+variant
            # FIXME: The following should be invalid:
            "sr@latin",  # language+script
        )
        self.invalid_tags = (
            None,  # invalid type: None.
            123,  # invalid type: int.
            b"en",  # invalid type: bytes.
            "eü",  # non-latin characters.
            "en_US",  # locale format.
            "en--us",  # empty subtag.
            "-en",  # leading separator.
            "en-",  # trailing separator.
            "en-US.UTF-8",  # language tag w/ locale encoding.
            "en_US.UTF-8",  # locale format - language w/ region and encoding.
            "ca_ES@valencia",  # locale format - language w/ region and variant.
            # FIXME: The following should be invalid:
            # 'sr@latin',      # locale instead of language tag.
        )