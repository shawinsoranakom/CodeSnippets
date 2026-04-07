def test_no_collision_for_proxy_models(self):
        class Model(models.Model):
            class Meta:
                db_table = "test_table"

        class ProxyModel(Model):
            class Meta:
                proxy = True

        self.assertEqual(Model._meta.db_table, ProxyModel._meta.db_table)
        self.assertEqual(checks.run_checks(app_configs=self.apps.get_app_configs()), [])