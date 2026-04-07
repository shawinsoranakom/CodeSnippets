def test_ticket7256(self):
        # An empty values() call includes all aliases, including those from an
        # extra()
        sql = "case when %s > 2 then 1 else 0 end" % connection.ops.quote_name("rank")
        qs = Ranking.objects.extra(select={"good": sql})
        dicts = qs.values().order_by("id")
        for d in dicts:
            del d["id"]
            del d["author_id"]
        self.assertEqual(
            [sorted(d.items()) for d in dicts],
            [
                [("good", 0), ("rank", 2)],
                [("good", 0), ("rank", 1)],
                [("good", 1), ("rank", 3)],
            ],
        )