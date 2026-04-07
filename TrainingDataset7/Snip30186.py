def test_traverse_qs(self):
        qs = Person.objects.prefetch_related("houses")
        related_objs_normal = ([list(p.houses.all()) for p in qs],)
        related_objs_from_traverse = [
            [inner[0] for inner in o[1]] for o in self.traverse_qs(qs, [["houses"]])
        ]
        self.assertEqual(related_objs_normal, (related_objs_from_traverse,))