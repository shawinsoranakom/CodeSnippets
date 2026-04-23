def test_ifchanged_concurrency(self):
        """
        #15849 -- ifchanged should be thread-safe.
        """
        template = self.engine.from_string(
            "[0{% for x in foo %},{% with var=get_value %}{% ifchanged %}"
            "{{ var }}{% endifchanged %}{% endwith %}{% endfor %}]"
        )

        # Using generator to mimic concurrency.
        # The generator is not passed to the 'for' loop, because it does a
        # list(values) instead, call gen.next() in the template to control the
        # generator.
        def gen():
            yield 1
            yield 2
            # Simulate that another thread is now rendering.
            # When the IfChangeNode stores state at 'self' it stays at '3' and
            # skip the last yielded value below.
            iter2 = iter([1, 2, 3])
            output2 = template.render(
                Context({"foo": range(3), "get_value": lambda: next(iter2)})
            )
            self.assertEqual(
                output2,
                "[0,1,2,3]",
                "Expected [0,1,2,3] in second parallel template, got {}".format(
                    output2
                ),
            )
            yield 3

        gen1 = gen()
        output1 = template.render(
            Context({"foo": range(3), "get_value": lambda: next(gen1)})
        )
        self.assertEqual(
            output1,
            "[0,1,2,3]",
            "Expected [0,1,2,3] in first template, got {}".format(output1),
        )