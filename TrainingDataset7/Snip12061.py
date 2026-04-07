def get_current_prefetch_to(self, level):
        return LOOKUP_SEP.join(self.prefetch_to.split(LOOKUP_SEP)[: level + 1])