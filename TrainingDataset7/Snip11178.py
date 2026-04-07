def __init__(
        self, *args, max_length=50, db_index=True, allow_unicode=False, **kwargs
    ):
        self.allow_unicode = allow_unicode
        if self.allow_unicode:
            self.default_validators = [validators.validate_unicode_slug]
        super().__init__(*args, max_length=max_length, db_index=db_index, **kwargs)