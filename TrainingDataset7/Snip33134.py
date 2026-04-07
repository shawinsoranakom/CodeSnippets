def test_title1(self):
        output = self.engine.render_to_string("title1", {"a": "JOE'S CRAB SHACK"})
        self.assertEqual(output, "Joe&#x27;s Crab Shack")