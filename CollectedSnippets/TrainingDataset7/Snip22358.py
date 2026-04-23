def test_force_insert_not_bool_or_tuple(self):
        msg = "force_insert must be a bool or tuple."
        with self.assertRaisesMessage(TypeError, msg), transaction.atomic():
            Counter().save(force_insert=1)
        with self.assertRaisesMessage(TypeError, msg), transaction.atomic():
            Counter().save(force_insert="test")
        with self.assertRaisesMessage(TypeError, msg), transaction.atomic():
            Counter().save(force_insert=[])