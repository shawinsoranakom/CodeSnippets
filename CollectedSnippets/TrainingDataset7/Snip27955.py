def test_width_height_correct_name_mangling_correct(self):
        instance1 = PersonNoReadImage()

        instance1.mugshot.save("mug", self.file1)

        self.assertEqual(instance1.mugshot_width, 4)
        self.assertEqual(instance1.mugshot_height, 8)

        instance1.save()

        self.assertEqual(instance1.mugshot_width, 4)
        self.assertEqual(instance1.mugshot_height, 8)

        instance2 = PersonNoReadImage()
        instance2.mugshot.save("mug", self.file1)
        instance2.save()

        self.assertNotEqual(instance1.mugshot.name, instance2.mugshot.name)

        self.assertEqual(instance1.mugshot_width, instance2.mugshot_width)
        self.assertEqual(instance1.mugshot_height, instance2.mugshot_height)