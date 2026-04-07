def safe_summary(self, encoded):
        decoded = self.decode(encoded)
        return {
            _("algorithm"): decoded["algorithm"],
            _("salt"): mask_hash(decoded["salt"], show=2),
            _("hash"): mask_hash(decoded["hash"]),
        }