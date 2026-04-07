def test_check_constraints_sql_keywords(self):
        with transaction.atomic():
            obj = SQLKeywordsModel.objects.create(reporter=self.r)
            obj.refresh_from_db()
            obj.reporter_id = 30
            with connection.constraint_checks_disabled():
                obj.save()
                try:
                    connection.check_constraints(table_names=["order"])
                except IntegrityError:
                    pass
                else:
                    self.skipTest("This backend does not support integrity checks.")
            transaction.set_rollback(True)