def prohibits_null_characters_in_text_exception(self):
        if is_psycopg3:
            return DataError, "PostgreSQL text fields cannot contain NUL (0x00) bytes"
        else:
            return ValueError, "A string literal cannot contain NUL (0x00) characters."