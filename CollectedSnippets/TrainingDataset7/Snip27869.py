def test_refresh_from_db(self):
        d = Document.objects.create(myfile="something.txt")
        d.refresh_from_db()
        self.assertIs(d.myfile.instance, d)