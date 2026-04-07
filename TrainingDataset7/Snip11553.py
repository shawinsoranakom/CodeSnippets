def count(self):
            if (
                superclass is Manager
                and self.get_prefetch_cache() is None
                and (constrained_target := self.constrained_target) is not None
            ):
                return constrained_target.count()
            else:
                return super().count()