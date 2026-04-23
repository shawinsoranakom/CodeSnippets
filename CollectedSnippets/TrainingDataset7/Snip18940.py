def test_manager_methods(self):
        """
        This test ensures that the correct set of methods from `QuerySet`
        are copied onto `Manager`.

        It's particularly useful to prevent accidentally leaking new methods
        into `Manager`. New `QuerySet` methods that should also be copied onto
        `Manager` will need to be added to
        `ManagerTest.QUERYSET_PROXY_METHODS`.
        """
        self.assertEqual(
            sorted(BaseManager._get_queryset_methods(models.QuerySet)),
            sorted(self.QUERYSET_PROXY_METHODS),
        )