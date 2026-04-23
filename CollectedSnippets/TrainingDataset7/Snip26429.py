def test_custom_max_lengths(self):
        self.verify_max_length(PersonWithCustomMaxLengths, "email", 250)
        self.verify_max_length(PersonWithCustomMaxLengths, "vcard", 250)
        self.verify_max_length(PersonWithCustomMaxLengths, "homepage", 250)
        self.verify_max_length(PersonWithCustomMaxLengths, "avatar", 250)