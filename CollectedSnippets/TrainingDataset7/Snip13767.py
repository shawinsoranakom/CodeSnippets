def __init__(self, seed=None):
        if seed is None:
            # Limit seeds to 10 digits for simpler output.
            seed = random.randint(0, 10**10 - 1)
            seed_source = "generated"
        else:
            seed_source = "given"
        self.seed = seed
        self.seed_source = seed_source