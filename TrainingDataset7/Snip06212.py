def safe_summary(self, encoded):
        decoded = self.decode(encoded)
        return {
            _("algorithm"): decoded["algorithm"],
            _("iterations"): decoded["iterations"],
            _("salt"): mask_hash(decoded["salt"]),
            _("hash"): mask_hash(decoded["hash"]),
        }