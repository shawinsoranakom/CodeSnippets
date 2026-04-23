def test_saving_and_querying_for_sql_null(self):
        obj = OtherTypesArrayModel.objects.create(json=[None, None])
        self.assertSequenceEqual(
            OtherTypesArrayModel.objects.filter(json__1__isnull=True), [obj]
        )
        # RemovedInDjango70Warning.
        msg = (
            "Using None as the right-hand side of an exact lookup on JSONField to mean "
            "JSON scalar 'null' is deprecated. Use JSONNull() instead (or use the "
            "__isnull lookup if you meant SQL NULL)."
        )
        with self.assertWarnsMessage(RemovedInDjango70Warning, msg):
            # RemovedInDjango70Warning: deindent, and replace [] with [obj].
            self.assertSequenceEqual(
                OtherTypesArrayModel.objects.filter(json__1=None), []
            )