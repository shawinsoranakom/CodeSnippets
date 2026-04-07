def test_queryset_with_custom_init(self):
        """
        BaseManager.get_queryset() should use kwargs rather than args to allow
        custom kwargs (#24911).
        """
        qs_custom = Person.custom_init_queryset_manager.all()
        qs_default = Person.objects.all()
        self.assertQuerySetEqual(qs_custom, qs_default)