def setUpTestData(cls):
        cls.foo1 = Foo.objects.create(a="a", d="12.34")
        cls.foo2 = Foo.objects.create(a="b", d="12.34")
        cls.bar1 = Bar.objects.create(a=cls.foo1, b="b")
        cls.bar2 = Bar.objects.create(a=cls.foo2, b="a")
        cls.field = Bar._meta.get_field("a")