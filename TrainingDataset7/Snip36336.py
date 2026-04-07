def test_cached_property_reuse_different_names(self):
        """
        Disallow this case because the decorated function wouldn't be cached.
        """
        type_msg = (
            "Cannot assign the same cached_property to two different names ('a' and "
            "'b')."
        )
        error_type = TypeError
        msg = type_msg

        with self.assertRaisesMessage(error_type, msg):

            class ReusedCachedProperty:
                @cached_property
                def a(self):
                    pass

                b = a