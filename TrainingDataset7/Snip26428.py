def test_default_max_lengths(self):
        self.verify_max_length(PersonWithDefaultMaxLengths, "email", 254)
        self.verify_max_length(PersonWithDefaultMaxLengths, "vcard", 100)
        self.verify_max_length(PersonWithDefaultMaxLengths, "homepage", 200)
        self.verify_max_length(PersonWithDefaultMaxLengths, "avatar", 100)