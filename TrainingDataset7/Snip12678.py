def validate_no_null_characters(self, value):
        non_null_character_validator = ProhibitNullCharactersValidator()
        return non_null_character_validator(value)