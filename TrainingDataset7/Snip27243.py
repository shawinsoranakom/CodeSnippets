def tearDown(self):
        # Unapply records on databases that don't roll back changes after each
        # test method.
        if not connection.features.supports_transactions:
            for recorder, app, name in self.applied_records:
                recorder.record_unapplied(app, name)