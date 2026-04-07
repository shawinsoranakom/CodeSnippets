def test_join_trimming_forwards(self):
        """
        Too many copies of the intermediate table aren't involved when doing a
        join (#8046, #8254).
        """
        self.assertSequenceEqual(
            self.rock.members.filter(membership__price=50),
            [self.jim],
        )