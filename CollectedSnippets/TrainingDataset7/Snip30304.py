def test_proxy_model_signals(self):
        """
        Test save signals for proxy models
        """
        output = []

        def make_handler(model, event):
            def _handler(*args, **kwargs):
                output.append("%s %s save" % (model, event))

            return _handler

        h1 = make_handler("MyPerson", "pre")
        h2 = make_handler("MyPerson", "post")
        h3 = make_handler("Person", "pre")
        h4 = make_handler("Person", "post")

        signals.pre_save.connect(h1, sender=MyPerson)
        signals.post_save.connect(h2, sender=MyPerson)
        signals.pre_save.connect(h3, sender=Person)
        signals.post_save.connect(h4, sender=Person)

        MyPerson.objects.create(name="dino")
        self.assertEqual(output, ["MyPerson pre save", "MyPerson post save"])

        output = []

        h5 = make_handler("MyPersonProxy", "pre")
        h6 = make_handler("MyPersonProxy", "post")

        signals.pre_save.connect(h5, sender=MyPersonProxy)
        signals.post_save.connect(h6, sender=MyPersonProxy)

        MyPersonProxy.objects.create(name="pebbles")

        self.assertEqual(output, ["MyPersonProxy pre save", "MyPersonProxy post save"])

        signals.pre_save.disconnect(h1, sender=MyPerson)
        signals.post_save.disconnect(h2, sender=MyPerson)
        signals.pre_save.disconnect(h3, sender=Person)
        signals.post_save.disconnect(h4, sender=Person)
        signals.pre_save.disconnect(h5, sender=MyPersonProxy)
        signals.post_save.disconnect(h6, sender=MyPersonProxy)