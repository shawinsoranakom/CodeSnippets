def test_self_relation(self):
        item1 = LinkedList.objects.create(name="item1")
        LinkedList.objects.create(name="item2", previous_item=item1)
        with self.assertNumQueries(1):
            item1_db = LinkedList.objects.select_related("next_item").get(name="item1")
            self.assertEqual(item1_db.next_item.name, "item2")