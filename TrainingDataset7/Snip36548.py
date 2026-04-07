def __reduce_ex__(self, proto):
        self.quux = "quux"
        return super().__reduce_ex__(proto)