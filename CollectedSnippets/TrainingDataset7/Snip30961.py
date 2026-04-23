def assertNoAnnotations(self, results):
        """
        The results of a raw query contain no annotations
        """
        self.assertAnnotations(results, ())