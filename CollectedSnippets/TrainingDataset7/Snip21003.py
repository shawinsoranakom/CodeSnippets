def assert_delayed(self, obj, num):
        """
        Instances with deferred fields look the same as normal instances when
        we examine attribute values. Therefore, this method returns the number
        of deferred fields on returned instances.
        """
        count = len(obj.get_deferred_fields())
        self.assertEqual(count, num)