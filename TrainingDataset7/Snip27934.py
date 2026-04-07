def check_dimensions(self, instance, width, height, field_name="mugshot"):
        """
        Asserts that the given width and height values match both the
        field's height and width attributes and the height and width fields
        (if defined) the image field is caching to.

        Note, this method will check for dimension fields named by adding
        "_width" or "_height" to the name of the ImageField. So, the
        models used in these tests must have their fields named
        accordingly.

        By default, we check the field named "mugshot", but this can be
        specified by passing the field_name parameter.
        """
        field = getattr(instance, field_name)
        # Check height/width attributes of field.
        if width is None and height is None:
            with self.assertRaises(ValueError):
                getattr(field, "width")
            with self.assertRaises(ValueError):
                getattr(field, "height")
        else:
            self.assertEqual(field.width, width)
            self.assertEqual(field.height, height)

        # Check height/width fields of model, if defined.
        width_field_name = field_name + "_width"
        if hasattr(instance, width_field_name):
            self.assertEqual(getattr(instance, width_field_name), width)
        height_field_name = field_name + "_height"
        if hasattr(instance, height_field_name):
            self.assertEqual(getattr(instance, height_field_name), height)