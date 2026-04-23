def test_complex_address_list(self):
        examples = list(self.example_params.values())
        source = ('dummy list:;, another: (empty);,' +
                 ', '.join([x[0] for x in examples[:4]]) + ', ' +
                 r'"A \"list\"": ' +
                    ', '.join([x[0] for x in examples[4:6]]) + ';,' +
                 ', '.join([x[0] for x in examples[6:]])
            )
        # XXX: the fact that (empty) disappears here is a potential API design
        # bug.  We don't currently have a way to preserve comments.
        expected = ('dummy list:;, another:;, ' +
                 ', '.join([x[2] for x in examples[:4]]) + ', ' +
                 r'"A \"list\"": ' +
                    ', '.join([x[2] for x in examples[4:6]]) + ';, ' +
                 ', '.join([x[2] for x in examples[6:]])
            )

        h = self.make_header('to', source)
        self.assertEqual(h.split(','), expected.split(','))
        self.assertEqual(h, expected)
        self.assertEqual(len(h.groups), 7 + len(examples) - 6)
        self.assertEqual(h.groups[0].display_name, 'dummy list')
        self.assertEqual(h.groups[1].display_name, 'another')
        self.assertEqual(h.groups[6].display_name, 'A "list"')
        self.assertEqual(len(h.addresses), len(examples))
        for i in range(4):
            self.assertIsNone(h.groups[i+2].display_name)
            self.assertEqual(str(h.groups[i+2].addresses[0]), examples[i][2])
        for i in range(7, 7 + len(examples) - 6):
            self.assertIsNone(h.groups[i].display_name)
            self.assertEqual(str(h.groups[i].addresses[0]), examples[i-1][2])
        for i in range(len(examples)):
            self.assertEqual(str(h.addresses[i]), examples[i][2])
            self.assertEqual(h.addresses[i].addr_spec, examples[i][4])