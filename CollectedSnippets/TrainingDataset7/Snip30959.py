def assertSuccessfulRawQuery(
        self,
        model,
        query,
        expected_results,
        expected_annotations=(),
        params=[],
        translations=None,
    ):
        """
        Execute the passed query against the passed model and check the output
        """
        results = list(
            model.objects.raw(query, params=params, translations=translations)
        )
        self.assertProcessed(model, results, expected_results, expected_annotations)
        self.assertAnnotations(results, expected_annotations)