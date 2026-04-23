def test_lookup_errors(self):
        m_tuple = "'%s' lookup of 'pk' must be a tuple or a list"
        m_2_elements = "'%s' lookup of 'pk' must have 2 elements"
        m_tuple_collection = (
            "'in' lookup of 'pk' must be a collection of tuples or lists"
        )
        m_2_elements_each = "'in' lookup of 'pk' must have 2 elements each"
        test_cases = (
            ({"pk": 1}, m_tuple % "exact"),
            ({"pk": (1, 2, 3)}, m_2_elements % "exact"),
            ({"pk__exact": 1}, m_tuple % "exact"),
            ({"pk__exact": (1, 2, 3)}, m_2_elements % "exact"),
            ({"pk__in": 1}, m_tuple % "in"),
            ({"pk__in": (1, 2, 3)}, m_tuple_collection),
            ({"pk__in": ((1, 2, 3),)}, m_2_elements_each),
            ({"pk__gt": 1}, m_tuple % "gt"),
            ({"pk__gt": (1, 2, 3)}, m_2_elements % "gt"),
            ({"pk__gte": 1}, m_tuple % "gte"),
            ({"pk__gte": (1, 2, 3)}, m_2_elements % "gte"),
            ({"pk__lt": 1}, m_tuple % "lt"),
            ({"pk__lt": (1, 2, 3)}, m_2_elements % "lt"),
            ({"pk__lte": 1}, m_tuple % "lte"),
            ({"pk__lte": (1, 2, 3)}, m_2_elements % "lte"),
        )

        for kwargs, message in test_cases:
            with (
                self.subTest(kwargs=kwargs),
                self.assertRaisesMessage(ValueError, message),
            ):
                Comment.objects.get(**kwargs)