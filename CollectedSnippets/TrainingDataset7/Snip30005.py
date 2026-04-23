def test_simple(self):
        searched = Line.objects.filter(dialogue__search="elbows")
        self.assertSequenceEqual(searched, [self.verse1])