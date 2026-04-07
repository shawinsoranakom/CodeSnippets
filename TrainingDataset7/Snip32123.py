def test_model_pre_init_and_post_init(self):
        data = []

        def pre_init_callback(sender, args, **kwargs):
            data.append(kwargs["kwargs"])

        signals.pre_init.connect(pre_init_callback)

        def post_init_callback(sender, instance, **kwargs):
            data.append(instance)

        signals.post_init.connect(post_init_callback)

        p1 = Person(first_name="John", last_name="Doe")
        self.assertEqual(data, [{}, p1])