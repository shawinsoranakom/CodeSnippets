def test_enqueue(self, container):
        dg = DeltaGenerator(root_container=container)
        self.assertEqual(0, dg._cursor.index)
        self.assertEqual(container, dg._root_container)

        test_data = "some test data"
        text_proto = TextProto()
        text_proto.body = test_data
        new_dg = dg._enqueue("text", text_proto)

        self.assertNotEqual(dg, new_dg)
        self.assertEqual(1, dg._cursor.index)
        self.assertEqual(container, new_dg._root_container)

        element = self.get_delta_from_queue().new_element
        self.assertEqual(element.text.body, test_data)