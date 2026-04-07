def test_get_fields_only_searches_forward_on_apps_not_ready(self):
        opts = Person._meta
        # If apps registry is not ready, get_field() searches over only
        # forward fields.
        opts.apps.models_ready = False
        try:
            # 'data_abstract' is a forward field, and therefore will be found
            self.assertTrue(opts.get_field("data_abstract"))
            msg = (
                "Person has no field named 'relating_baseperson'. The app "
                "cache isn't ready yet, so if this is an auto-created related "
                "field, it won't be available yet."
            )
            # 'data_abstract' is a reverse field, and will raise an exception
            with self.assertRaisesMessage(FieldDoesNotExist, msg):
                opts.get_field("relating_baseperson")
        finally:
            opts.apps.models_ready = True