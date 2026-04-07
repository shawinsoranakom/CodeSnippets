def test_image_field(self):
        # ImageField and FileField are nearly identical, but they differ
        # slightly when it comes to validation. This specifically tests that
        # #6302 is fixed for both file fields and image fields.

        with open(os.path.join(os.path.dirname(__file__), "test.png"), "rb") as fp:
            image_data = fp.read()
        with open(os.path.join(os.path.dirname(__file__), "test2.png"), "rb") as fp:
            image_data2 = fp.read()

        f = ImageFileForm(
            data={"description": "An image"},
            files={"image": SimpleUploadedFile("test.png", image_data)},
        )
        self.assertTrue(f.is_valid())
        self.assertEqual(type(f.cleaned_data["image"]), SimpleUploadedFile)
        instance = f.save()
        self.assertEqual(instance.image.name, "tests/test.png")
        self.assertEqual(instance.width, 16)
        self.assertEqual(instance.height, 16)

        # Delete the current file since this is not done by Django, but don't
        # save because the dimension fields are not null=True.
        instance.image.delete(save=False)
        f = ImageFileForm(
            data={"description": "An image"},
            files={"image": SimpleUploadedFile("test.png", image_data)},
        )
        self.assertTrue(f.is_valid())
        self.assertEqual(type(f.cleaned_data["image"]), SimpleUploadedFile)
        instance = f.save()
        self.assertEqual(instance.image.name, "tests/test.png")
        self.assertEqual(instance.width, 16)
        self.assertEqual(instance.height, 16)

        # Edit an instance that already has the (required) image defined in the
        # model. This will not save the image again, but leave it exactly as it
        # is.

        f = ImageFileForm(data={"description": "Look, it changed"}, instance=instance)
        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data["image"].name, "tests/test.png")
        instance = f.save()
        self.assertEqual(instance.image.name, "tests/test.png")
        self.assertEqual(instance.height, 16)
        self.assertEqual(instance.width, 16)

        # Delete the current file since this is not done by Django, but don't
        # save because the dimension fields are not null=True.
        instance.image.delete(save=False)
        # Override the file by uploading a new one.

        f = ImageFileForm(
            data={"description": "Changed it"},
            files={"image": SimpleUploadedFile("test2.png", image_data2)},
            instance=instance,
        )
        self.assertTrue(f.is_valid())
        instance = f.save()
        self.assertEqual(instance.image.name, "tests/test2.png")
        self.assertEqual(instance.height, 32)
        self.assertEqual(instance.width, 48)

        # Delete the current file since this is not done by Django, but don't
        # save because the dimension fields are not null=True.
        instance.image.delete(save=False)
        instance.delete()

        f = ImageFileForm(
            data={"description": "Changed it"},
            files={"image": SimpleUploadedFile("test2.png", image_data2)},
        )
        self.assertTrue(f.is_valid())
        instance = f.save()
        self.assertEqual(instance.image.name, "tests/test2.png")
        self.assertEqual(instance.height, 32)
        self.assertEqual(instance.width, 48)

        # Delete the current file since this is not done by Django, but don't
        # save because the dimension fields are not null=True.
        instance.image.delete(save=False)
        instance.delete()

        # Test the non-required ImageField
        # Note: In Oracle, we expect a null ImageField to return '' instead of
        # None.
        if connection.features.interprets_empty_strings_as_nulls:
            expected_null_imagefield_repr = ""
        else:
            expected_null_imagefield_repr = None

        f = OptionalImageFileForm(data={"description": "Test"})
        self.assertTrue(f.is_valid())
        instance = f.save()
        self.assertEqual(instance.image.name, expected_null_imagefield_repr)
        self.assertIsNone(instance.width)
        self.assertIsNone(instance.height)

        f = OptionalImageFileForm(
            data={"description": "And a final one"},
            files={"image": SimpleUploadedFile("test3.png", image_data)},
            instance=instance,
        )
        self.assertTrue(f.is_valid())
        instance = f.save()
        self.assertEqual(instance.image.name, "tests/test3.png")
        self.assertEqual(instance.width, 16)
        self.assertEqual(instance.height, 16)

        # Editing the instance without re-uploading the image should not affect
        # the image or its width/height properties.
        f = OptionalImageFileForm({"description": "New Description"}, instance=instance)
        self.assertTrue(f.is_valid())
        instance = f.save()
        self.assertEqual(instance.description, "New Description")
        self.assertEqual(instance.image.name, "tests/test3.png")
        self.assertEqual(instance.width, 16)
        self.assertEqual(instance.height, 16)

        # Delete the current file since this is not done by Django.
        instance.image.delete()
        instance.delete()

        f = OptionalImageFileForm(
            data={"description": "And a final one"},
            files={"image": SimpleUploadedFile("test4.png", image_data2)},
        )
        self.assertTrue(f.is_valid())
        instance = f.save()
        self.assertEqual(instance.image.name, "tests/test4.png")
        self.assertEqual(instance.width, 48)
        self.assertEqual(instance.height, 32)
        instance.delete()
        # Callable upload_to behavior that's dependent on the value of another
        # field in the model.
        f = ImageFileForm(
            data={"description": "And a final one", "path": "foo"},
            files={"image": SimpleUploadedFile("test4.png", image_data)},
        )
        self.assertTrue(f.is_valid())
        instance = f.save()
        self.assertEqual(instance.image.name, "foo/test4.png")
        instance.delete()

        # Editing an instance that has an image without an extension shouldn't
        # fail validation. First create:
        f = NoExtensionImageFileForm(
            data={"description": "An image"},
            files={"image": SimpleUploadedFile("test.png", image_data)},
        )
        self.assertTrue(f.is_valid())
        instance = f.save()
        self.assertEqual(instance.image.name, "tests/no_extension")
        # Then edit:
        f = NoExtensionImageFileForm(
            data={"description": "Edited image"}, instance=instance
        )
        self.assertTrue(f.is_valid())