def test_tenant_id(self):
        query = Query(User)
        path, final_field, targets, rest = query.names_to_path(
            ["tenant", "id"], User._meta
        )

        self.assertEqual(
            path,
            [
                PathInfo(
                    from_opts=User._meta,
                    to_opts=Tenant._meta,
                    target_fields=(Tenant._meta.get_field("id"),),
                    join_field=User._meta.get_field("tenant"),
                    m2m=False,
                    direct=True,
                    filtered_relation=None,
                ),
            ],
        )
        self.assertEqual(final_field, Tenant._meta.get_field("id"))
        self.assertEqual(targets, (Tenant._meta.get_field("id"),))
        self.assertEqual(rest, [])