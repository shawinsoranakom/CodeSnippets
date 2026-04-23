def test_decorators(self):
        data = []

        @receiver(signals.pre_save, weak=False)
        def decorated_handler(signal, sender, instance, **kwargs):
            data.append(instance)

        @receiver(signals.pre_save, sender=Car, weak=False)
        def decorated_handler_with_sender_arg(signal, sender, instance, **kwargs):
            data.append(instance)

        try:
            c1 = Car.objects.create(make="Volkswagen", model="Passat")
            self.assertEqual(data, [c1, c1])
        finally:
            signals.pre_save.disconnect(decorated_handler)
            signals.pre_save.disconnect(decorated_handler_with_sender_arg, sender=Car)