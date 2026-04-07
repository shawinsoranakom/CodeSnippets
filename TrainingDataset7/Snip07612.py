def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.signer = signing.get_cookie_signer(salt=self.key_salt)