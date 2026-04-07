def test_dumpdata_with_uuid_pks(self):
        m1 = PrimaryKeyUUIDModel.objects.create()
        m2 = PrimaryKeyUUIDModel.objects.create()
        output = StringIO()
        management.call_command(
            "dumpdata",
            "fixtures.PrimaryKeyUUIDModel",
            "--pks",
            ", ".join([str(m1.id), str(m2.id)]),
            stdout=output,
        )
        result = output.getvalue()
        self.assertIn('"pk": "%s"' % m1.id, result)
        self.assertIn('"pk": "%s"' % m2.id, result)