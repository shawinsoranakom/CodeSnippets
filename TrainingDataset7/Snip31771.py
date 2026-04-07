def test_serialize_progressbar(self):
        fake_stdout = StringIO()
        serializers.serialize(
            self.serializer_name,
            Article.objects.all(),
            progress_output=fake_stdout,
            object_count=Article.objects.count(),
        )
        self.assertTrue(
            fake_stdout.getvalue().endswith(
                "[" + "." * ProgressBar.progress_width + "]\n"
            )
        )