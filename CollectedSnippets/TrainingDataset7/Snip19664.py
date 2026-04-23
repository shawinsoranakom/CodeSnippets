def test_comments(self):
        query = Query(User)
        path, final_field, targets, rest = query.names_to_path(["comments"], User._meta)

        self.assertEqual(
            path,
            [
                PathInfo(
                    from_opts=User._meta,
                    to_opts=Comment._meta,
                    target_fields=(Comment._meta.get_field("pk"),),
                    join_field=User._meta.get_field("comments"),
                    m2m=True,
                    direct=False,
                    filtered_relation=None,
                ),
            ],
        )
        self.assertEqual(final_field, User._meta.get_field("comments"))
        self.assertEqual(targets, (Comment._meta.get_field("pk"),))
        self.assertEqual(rest, [])