def test_format_lazy(self):
        self.assertEqual("django/test", format_lazy("{}/{}", "django", lazystr("test")))
        self.assertEqual("django/test", format_lazy("{0}/{1}", *("django", "test")))
        self.assertEqual(
            "django/test", format_lazy("{a}/{b}", **{"a": "django", "b": "test"})
        )
        self.assertEqual(
            "django/test", format_lazy("{a[0]}/{a[1]}", a=("django", "test"))
        )

        t = {}
        s = format_lazy("{0[a]}-{p[a]}", t, p=t)
        t["a"] = lazystr("django")
        self.assertEqual("django-django", s)
        t["a"] = "update"
        self.assertEqual("update-update", s)

        # The format string can be lazy. (string comes from contrib.admin)
        s = format_lazy(
            gettext_lazy("Added {name} “{object}”."),
            name="article",
            object="My first try",
        )
        with override("fr"):
            self.assertEqual("Ajout de article «\xa0My first try\xa0».", s)