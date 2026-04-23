def safe_summary(self, encoded):
        decoded = self.decode(encoded)
        return {
            _("algorithm"): decoded["algorithm"],
            _("work factor"): decoded["work_factor"],
            _("block size"): decoded["block_size"],
            _("parallelism"): decoded["parallelism"],
            _("salt"): mask_hash(decoded["salt"]),
            _("hash"): mask_hash(decoded["hash"]),
        }