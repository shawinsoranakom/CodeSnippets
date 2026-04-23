def test_multi_table_inheritance_unsupported(self):
        expected_message = "Can't bulk create a multi-table inherited model"
        with self.assertRaisesMessage(ValueError, expected_message):
            Pizzeria.objects.bulk_create(
                [
                    Pizzeria(name="The Art of Pizza"),
                ]
            )
        with self.assertRaisesMessage(ValueError, expected_message):
            ProxyMultiCountry.objects.bulk_create(
                [
                    ProxyMultiCountry(name="Fillory", iso_two_letter="FL"),
                ]
            )
        with self.assertRaisesMessage(ValueError, expected_message):
            ProxyMultiProxyCountry.objects.bulk_create(
                [
                    ProxyMultiProxyCountry(name="Fillory", iso_two_letter="FL"),
                ]
            )