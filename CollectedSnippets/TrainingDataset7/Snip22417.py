def test_lookup_errors(self):
        m_2_elements = "'%s' lookup of 'customer' must have 2 elements"
        m_2_elements_each = "'in' lookup of 'customer' must have 2 elements each"
        test_cases = (
            ({"customer": 1}, m_2_elements % "exact"),
            ({"customer": (1, 2, 3)}, m_2_elements % "exact"),
            ({"customer__in": (1, 2, 3)}, m_2_elements_each),
            ({"customer__in": ("foo", "bar")}, m_2_elements_each),
            ({"customer__gt": 1}, m_2_elements % "gt"),
            ({"customer__gt": (1, 2, 3)}, m_2_elements % "gt"),
            ({"customer__gte": 1}, m_2_elements % "gte"),
            ({"customer__gte": (1, 2, 3)}, m_2_elements % "gte"),
            ({"customer__lt": 1}, m_2_elements % "lt"),
            ({"customer__lt": (1, 2, 3)}, m_2_elements % "lt"),
            ({"customer__lte": 1}, m_2_elements % "lte"),
            ({"customer__lte": (1, 2, 3)}, m_2_elements % "lte"),
        )

        for kwargs, message in test_cases:
            with (
                self.subTest(kwargs=kwargs),
                self.assertRaisesMessage(ValueError, message),
            ):
                Contact.objects.get(**kwargs)