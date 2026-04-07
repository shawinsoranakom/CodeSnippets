def setup_shuffler(self):
        if self.shuffle is False:
            return
        shuffler = Shuffler(seed=self.shuffle)
        self.log(f"Using shuffle seed: {shuffler.seed_display}")
        self._shuffler = shuffler