def test_is_pk_set(self):
        def new_instance():
            a = Article(pub_date=datetime.today())
            a.save()
            return a

        cases = [
            Article(id=1),
            Article(id=0),
            Article.objects.create(pub_date=datetime.today()),
            new_instance(),
        ]
        for case in cases:
            with self.subTest(case=case):
                self.assertIs(case._is_pk_set(), True)