def test_query_combined_mismatch(self):
        msg = (
            "SearchQuery can only be combined with other SearchQuery "
            "instances, got NoneType."
        )
        with self.assertRaisesMessage(TypeError, msg):
            Line.objects.filter(dialogue__search=None | SearchQuery("kneecaps"))

        with self.assertRaisesMessage(TypeError, msg):
            Line.objects.filter(dialogue__search=None & SearchQuery("kneecaps"))