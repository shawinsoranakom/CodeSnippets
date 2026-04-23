def safe_summary(self, encoded):
        decoded = self.decode(encoded)
        return {
            _("algorithm"): decoded["algorithm"],
            _("variety"): decoded["variety"],
            _("version"): decoded["version"],
            _("memory cost"): decoded["memory_cost"],
            _("time cost"): decoded["time_cost"],
            _("parallelism"): decoded["parallelism"],
            _("salt"): mask_hash(decoded["salt"]),
            _("hash"): mask_hash(decoded["hash"]),
        }