def test_write_base_many2many(self):
        """ Write on many2many field. """
        rec1 = self.env['test_performance.base'].create({'name': 'X'})

        # create N tags on rec1: O(1) queries
        with self.assertQueryCount(4):
            self.env.invalidate_all()
            rec1.write({'tag_ids': [Command.create({'name': 0})]})
        self.assertEqual(len(rec1.tag_ids), 1)

        with self.assertQueryCount(4):
            self.env.invalidate_all()
            rec1.write({'tag_ids': [Command.create({'name': val}) for val in range(1, 12)]})
        self.assertEqual(len(rec1.tag_ids), 12)

        tags = rec1.tag_ids

        # update N tags: O(N) queries
        with self.assertQueryCount(3):
            self.env.invalidate_all()
            rec1.write({'tag_ids': [Command.update(tag.id, {'name': 'X'}) for tag in tags[0]]})
        self.assertEqual(rec1.tag_ids, tags)

        with self.assertQueryCount(3):
            self.env.invalidate_all()
            rec1.write({'tag_ids': [Command.update(tag.id, {'name': 'X'}) for tag in tags[1:]]})
        self.assertEqual(rec1.tag_ids, tags)

        # delete N tags: O(1) queries
        with self.assertQueryCount(__system__=6, demo=6):
            self.env.invalidate_all()
            rec1.write({'tag_ids': [Command.delete(tag.id) for tag in tags[0]]})
        self.assertEqual(rec1.tag_ids, tags[1:])

        with self.assertQueryCount(__system__=6, demo=6):
            self.env.invalidate_all()
            rec1.write({'tag_ids': [Command.delete(tag.id) for tag in tags[1:]]})
        self.assertFalse(rec1.tag_ids)
        self.assertFalse(tags.exists())

        rec1.write({'tag_ids': [Command.create({'name': val}) for val in range(12)]})
        tags = rec1.tag_ids

        # unlink N tags: O(1) queries
        with self.assertQueryCount(3):
            self.env.invalidate_all()
            rec1.write({'tag_ids': [Command.unlink(tag.id) for tag in tags[0]]})
        self.assertEqual(rec1.tag_ids, tags[1:])

        with self.assertQueryCount(3):
            self.env.invalidate_all()
            rec1.write({'tag_ids': [Command.unlink(tag.id) for tag in tags[1:]]})
        self.assertFalse(rec1.tag_ids)
        self.assertTrue(tags.exists())

        rec2 = self.env['test_performance.base'].create({'name': 'X'})

        # link N tags from rec1 to rec2: O(1) queries
        with self.assertQueryCount(3):
            self.env.invalidate_all()
            rec2.write({'tag_ids': [Command.link(tag.id) for tag in tags[0]]})
        self.assertEqual(rec2.tag_ids, tags[0])

        with self.assertQueryCount(3):
            self.env.invalidate_all()
            rec2.write({'tag_ids': [Command.link(tag.id) for tag in tags[1:]]})
        self.assertEqual(rec2.tag_ids, tags)

        with self.assertQueryCount(2):
            self.env.invalidate_all()
            rec2.write({'tag_ids': [Command.link(tag.id) for tag in tags[1:]]})
        self.assertEqual(rec2.tag_ids, tags)

        # empty N tags in rec2: O(1) queries
        with self.assertQueryCount(3):
            self.env.invalidate_all()
            rec2.write({'tag_ids': [Command.clear()]})
        self.assertFalse(rec2.tag_ids)
        self.assertTrue(tags.exists())

        with self.assertQueryCount(2):
            self.env.invalidate_all()
            rec2.write({'tag_ids': [Command.clear()]})
        self.assertFalse(rec2.tag_ids)

        # set N tags in rec2: O(1) queries
        with self.assertQueryCount(3):
            self.env.invalidate_all()
            rec2.write({'tag_ids': [Command.set(tags.ids)]})
        self.assertEqual(rec2.tag_ids, tags)

        with self.assertQueryCount(3):
            self.env.invalidate_all()
            rec2.write({'tag_ids': [Command.set(tags[:8].ids)]})
        self.assertEqual(rec2.tag_ids, tags[:8])

        with self.assertQueryCount(4):
            self.env.invalidate_all()
            rec2.write({'tag_ids': [Command.set(tags[4:].ids)]})
        self.assertEqual(rec2.tag_ids, tags[4:])

        with self.assertQueryCount(3):
            self.env.invalidate_all()
            rec2.write({'tag_ids': [Command.set(tags.ids)]})
        self.assertEqual(rec2.tag_ids, tags)

        with self.assertQueryCount(2):
            self.env.invalidate_all()
            rec2.write({'tag_ids': [Command.set(tags.ids)]})
        self.assertEqual(rec2.tag_ids, tags)