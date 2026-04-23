def exists(self):
            if (
                superclass is Manager
                and self.get_prefetch_cache() is None
                and (constrained_target := self.constrained_target) is not None
            ):
                return constrained_target.exists()
            else:
                return super().exists()