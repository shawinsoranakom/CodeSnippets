def test_defer(self):
        Document.objects.create(myfile="something.txt")
        self.assertEqual(Document.objects.defer("myfile")[0].myfile, "something.txt")