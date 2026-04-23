def test_add_rejects_wrong_instances(self):
        msg = "'TaggedItem' instance expected, got <Animal: Lion>"
        with self.assertRaisesMessage(TypeError, msg):
            self.bacon.tags.add(self.lion)