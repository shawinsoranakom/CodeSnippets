def assertAnnotations(self, results, expected_annotations):
        """
        The passed raw query results contain the expected annotations
        """
        if expected_annotations:
            for index, result in enumerate(results):
                annotation, value = expected_annotations[index]
                self.assertTrue(hasattr(result, annotation))
                self.assertEqual(getattr(result, annotation), value)