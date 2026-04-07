def assertProcessed(self, model, results, orig, expected_annotations=()):
        """
        Compare the results of a raw query against expected results
        """
        self.assertEqual(len(results), len(orig))
        for index, item in enumerate(results):
            orig_item = orig[index]
            for annotation in expected_annotations:
                setattr(orig_item, *annotation)

            for field in model._meta.fields:
                # All values on the model are equal
                self.assertEqual(
                    getattr(item, field.attname), getattr(orig_item, field.attname)
                )
                # This includes checking that they are the same type
                self.assertEqual(
                    type(getattr(item, field.attname)),
                    type(getattr(orig_item, field.attname)),
                )