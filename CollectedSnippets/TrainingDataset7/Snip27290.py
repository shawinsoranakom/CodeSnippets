def test_create_model4(self):
        """
        Test multiple routers.
        """
        with override_settings(DATABASE_ROUTERS=[AgnosticRouter(), AgnosticRouter()]):
            self._test_create_model("test_mltdb_crmo4", should_run=True)
        with override_settings(
            DATABASE_ROUTERS=[MigrateNothingRouter(), MigrateEverythingRouter()]
        ):
            self._test_create_model("test_mltdb_crmo4", should_run=False)
        with override_settings(
            DATABASE_ROUTERS=[MigrateEverythingRouter(), MigrateNothingRouter()]
        ):
            self._test_create_model("test_mltdb_crmo4", should_run=True)