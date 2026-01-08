class QuadraticProbing(HashTable):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _collision_resolution(self, key, data=None):
        i = 1
        new_key = self.hash_function(key + i * i)

        while self.values[new_key] is not None and self.values[new_key] != key:
            i += 1
            new_key = (
                self.hash_function(key + i * i)
                if not self.balanced_factor() >= self.lim_charge
                else None
            )

            if new_key is None:
                break

        return new_key

