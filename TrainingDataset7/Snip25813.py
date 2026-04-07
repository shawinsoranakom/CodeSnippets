def test_values_list_extra(self):
        self.assertSequenceEqual(
            Article.objects.extra(select={"id_plus_one": "id+1"})
            .order_by("id")
            .values_list("id"),
            [
                (self.a1.id,),
                (self.a2.id,),
                (self.a3.id,),
                (self.a4.id,),
                (self.a5.id,),
                (self.a6.id,),
                (self.a7.id,),
            ],
        )
        self.assertSequenceEqual(
            Article.objects.extra(select={"id_plus_one": "id+1"})
            .order_by("id")
            .values_list("id_plus_one", "id"),
            [
                (self.a1.id + 1, self.a1.id),
                (self.a2.id + 1, self.a2.id),
                (self.a3.id + 1, self.a3.id),
                (self.a4.id + 1, self.a4.id),
                (self.a5.id + 1, self.a5.id),
                (self.a6.id + 1, self.a6.id),
                (self.a7.id + 1, self.a7.id),
            ],
        )
        self.assertSequenceEqual(
            Article.objects.extra(select={"id_plus_one": "id+1"})
            .order_by("id")
            .values_list("id", "id_plus_one"),
            [
                (self.a1.id, self.a1.id + 1),
                (self.a2.id, self.a2.id + 1),
                (self.a3.id, self.a3.id + 1),
                (self.a4.id, self.a4.id + 1),
                (self.a5.id, self.a5.id + 1),
                (self.a6.id, self.a6.id + 1),
                (self.a7.id, self.a7.id + 1),
            ],
        )