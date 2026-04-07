def test_passes_on_record(self):
        collector = []

        def _callback(record):
            collector.append(record)
            return True

        f = CallbackFilter(_callback)

        f.filter("a record")

        self.assertEqual(collector, ["a record"])