def test_get_author_m2m_relation(self):
        self.assertSequenceEqual(
            self.article.authors.filter(last_name="Jones"), [self.a2]
        )