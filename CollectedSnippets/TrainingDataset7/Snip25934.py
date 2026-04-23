def test_pk_set_on_repeated_add_remove(self):
        """
        m2m_changed is always fired, even for repeated calls to the same
        method, but the behavior of pk_sets differs by action.

        - For signals related to `add()`, only PKs that will actually be
          inserted are sent.
        - For `remove()` all PKs are sent, even if they will not affect the DB.
        """
        pk_sets_sent = []

        def handler(signal, sender, **kwargs):
            if kwargs["action"] in ["pre_add", "pre_remove"]:
                pk_sets_sent.append(kwargs["pk_set"])

        models.signals.m2m_changed.connect(handler, Car.default_parts.through)

        self.vw.default_parts.add(self.wheelset)
        self.vw.default_parts.add(self.wheelset)

        self.vw.default_parts.remove(self.wheelset)
        self.vw.default_parts.remove(self.wheelset)

        expected_pk_sets = [
            {self.wheelset.pk},
            set(),
            {self.wheelset.pk},
            {self.wheelset.pk},
        ]
        self.assertEqual(pk_sets_sent, expected_pk_sets)

        models.signals.m2m_changed.disconnect(handler, Car.default_parts.through)