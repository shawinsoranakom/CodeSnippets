def test_microseconds(self):
        Article.objects.create(
            title="How to Django",
            text=lorem_ipsum,
            written=timezone.now(),
        )
        now_string = (
            Article.objects.annotate(now_string=Cast(Now(), TextField()))
            .get()
            .now_string
        )
        precision = connection.features.time_cast_precision
        self.assertRegex(now_string, rf"^.*\.\d{{1,{precision}}}")