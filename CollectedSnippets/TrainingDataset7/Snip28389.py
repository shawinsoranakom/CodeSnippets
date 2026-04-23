def create_basic_data(self):
        self.c1 = Category.objects.create(
            name="Entertainment", slug="entertainment", url="entertainment"
        )
        self.c2 = Category.objects.create(
            name="It's a test", slug="its-test", url="test"
        )
        self.c3 = Category.objects.create(
            name="Third test", slug="third-test", url="third"
        )
        self.w_royko = Writer.objects.create(name="Mike Royko")
        self.w_woodward = Writer.objects.create(name="Bob Woodward")