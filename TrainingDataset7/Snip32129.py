def test_save_and_delete_signals_with_m2m(self):
        data = []

        def pre_save_handler(signal, sender, instance, **kwargs):
            data.append("pre_save signal, %s" % instance)
            if kwargs.get("raw"):
                data.append("Is raw")

        def post_save_handler(signal, sender, instance, **kwargs):
            data.append("post_save signal, %s" % instance)
            if "created" in kwargs:
                if kwargs["created"]:
                    data.append("Is created")
                else:
                    data.append("Is updated")
            if kwargs.get("raw"):
                data.append("Is raw")

        def pre_delete_handler(signal, sender, instance, **kwargs):
            data.append("pre_delete signal, %s" % instance)
            data.append("instance.id is not None: %s" % (instance.id is not None))

        def post_delete_handler(signal, sender, instance, **kwargs):
            data.append("post_delete signal, %s" % instance)
            data.append("instance.id is not None: %s" % (instance.id is not None))

        signals.pre_save.connect(pre_save_handler, weak=False)
        signals.post_save.connect(post_save_handler, weak=False)
        signals.pre_delete.connect(pre_delete_handler, weak=False)
        signals.post_delete.connect(post_delete_handler, weak=False)
        try:
            a1 = Author.objects.create(name="Neal Stephenson")
            self.assertEqual(
                data,
                [
                    "pre_save signal, Neal Stephenson",
                    "post_save signal, Neal Stephenson",
                    "Is created",
                ],
            )
            data[:] = []

            b1 = Book.objects.create(name="Snow Crash")
            self.assertEqual(
                data,
                [
                    "pre_save signal, Snow Crash",
                    "post_save signal, Snow Crash",
                    "Is created",
                ],
            )
            data[:] = []

            # Assigning and removing to/from m2m shouldn't generate an m2m
            # signal.
            b1.authors.set([a1])
            self.assertEqual(data, [])
            b1.authors.set([])
            self.assertEqual(data, [])
        finally:
            signals.pre_save.disconnect(pre_save_handler)
            signals.post_save.disconnect(post_save_handler)
            signals.pre_delete.disconnect(pre_delete_handler)
            signals.post_delete.disconnect(post_delete_handler)