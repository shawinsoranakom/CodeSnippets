def test_transform(self):
        new_name = self.t1.name.upper()
        self.assertNotEqual(self.t1.name, new_name)
        Tag.objects.create(name=new_name)
        with register_lookup(CharField, Lower):
            self.assertCountEqual(
                Tag.objects.order_by().distinct("name__lower"),
                [self.t1, self.t2, self.t3, self.t4, self.t5],
            )