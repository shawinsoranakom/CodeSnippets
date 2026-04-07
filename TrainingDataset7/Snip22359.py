def test_force_insert_not_model(self):
        msg = f"Invalid force_insert member. {object!r} must be a model subclass."
        with self.assertRaisesMessage(TypeError, msg), transaction.atomic():
            Counter().save(force_insert=(object,))
        instance = Counter()
        msg = f"Invalid force_insert member. {instance!r} must be a model subclass."
        with self.assertRaisesMessage(TypeError, msg), transaction.atomic():
            Counter().save(force_insert=(instance,))