def generate_hash(self, values):
        return hashlib.sha1("|".join(values).encode()).hexdigest()