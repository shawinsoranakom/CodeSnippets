def safe_summary(self, encoded):
        decoded = self.decode(encoded)
        return {
            _("algorithm"): decoded["algorithm"],
            _("work factor"): decoded["work_factor"],
            _("salt"): mask_hash(decoded["salt"]),
            _("checksum"): mask_hash(decoded["checksum"]),
        }