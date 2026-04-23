def test_write_base_one2many(self):
        """ Write on one2many field. """
        rec1 = self.env['test_performance.base'].create({'name': 'X'})

        # create N lines on rec1: O(1) queries
        with self.assertQueryCount(3):
            self.env.invalidate_all()
            rec1.write({'line_ids': [Command.create({'value': 0})]})
        self.assertEqual(len(rec1.line_ids), 1)

        with self.assertQueryCount(4):
            self.env.invalidate_all()
            rec1.write({'line_ids': [Command.create({'value': val}) for val in range(1, 12)]})
        self.assertEqual(len(rec1.line_ids), 12)

        lines = rec1.line_ids

        # update N lines: O(1) queries
        with self.assertQueryCount(4):
            self.env.invalidate_all()
            rec1.write({'line_ids': [Command.update(line.id, {'value': 42}) for line in lines[0]]})
        self.assertEqual(rec1.line_ids, lines)

        with self.assertQueryCount(4):
            self.env.invalidate_all()
            rec1.write({'line_ids': [Command.update(line.id, {'value': 42 + line.id}) for line in lines[1:]]})
        self.assertEqual(rec1.line_ids, lines)

        # delete N lines: O(1) queries
        with self.assertQueryCount(10):
            self.env.invalidate_all()
            rec1.write({'line_ids': [Command.delete(line.id) for line in lines[0]]})
        self.assertEqual(rec1.line_ids, lines[1:])

        with self.assertQueryCount(9):
            self.env.invalidate_all()
            rec1.write({'line_ids': [Command.delete(line.id) for line in lines[1:]]})
        self.assertFalse(rec1.line_ids)
        self.assertFalse(lines.exists())

        rec1.write({'line_ids': [Command.create({'value': val}) for val in range(12)]})
        lines = rec1.line_ids

        # unlink N lines: O(1) queries
        with self.assertQueryCount(10):
            self.env.invalidate_all()
            rec1.write({'line_ids': [Command.unlink(line.id) for line in lines[0]]})
        self.assertEqual(rec1.line_ids, lines[1:])

        with self.assertQueryCount(9):
            self.env.invalidate_all()
            rec1.write({'line_ids': [Command.unlink(line.id) for line in lines[1:]]})
        self.assertFalse(rec1.line_ids)
        self.assertFalse(lines.exists())

        rec1.write({'line_ids': [Command.create({'value': val}) for val in range(12)]})
        lines = rec1.line_ids
        rec2 = self.env['test_performance.base'].create({'name': 'X'})

        # link N lines from rec1 to rec2: O(1) queries
        with self.assertQueryCount(6):
            self.env.invalidate_all()
            rec2.write({'line_ids': [Command.link(line.id) for line in lines[0]]})
        self.assertEqual(rec1.line_ids, lines[1:])
        self.assertEqual(rec2.line_ids, lines[0])

        with self.assertQueryCount(6):
            self.env.invalidate_all()
            rec2.write({'line_ids': [Command.link(line.id) for line in lines[1:]]})
        self.assertFalse(rec1.line_ids)
        self.assertEqual(rec2.line_ids, lines)

        with self.assertQueryCount(3):
            self.env.invalidate_all()
            rec2.write({'line_ids': [Command.link(line.id) for line in lines[0]]})
        self.assertEqual(rec2.line_ids, lines)

        with self.assertQueryCount(3):
            self.env.invalidate_all()
            rec2.write({'line_ids': [Command.link(line.id) for line in lines[1:]]})
        self.assertEqual(rec2.line_ids, lines)

        # empty N lines in rec2: O(1) queries
        with self.assertQueryCount(10):
            self.env.invalidate_all()
            rec2.write({'line_ids': [Command.clear()]})
        self.assertFalse(rec2.line_ids)

        with self.assertQueryCount(3):
            self.env.invalidate_all()
            rec2.write({'line_ids': [Command.clear()]})
        self.assertFalse(rec2.line_ids)

        rec1.write({'line_ids': [Command.create({'value': val}) for val in range(12)]})
        lines = rec1.line_ids

        # set N lines in rec2: O(1) queries
        with self.assertQueryCount(6):
            self.env.invalidate_all()
            rec2.write({'line_ids': [Command.set(lines[0].ids)]})
        self.assertEqual(rec1.line_ids, lines[1:])
        self.assertEqual(rec2.line_ids, lines[0])

        with self.assertQueryCount(5):
            self.env.invalidate_all()
            rec2.write({'line_ids': [Command.set(lines.ids)]})
        self.assertFalse(rec1.line_ids)
        self.assertEqual(rec2.line_ids, lines)

        with self.assertQueryCount(4):
            self.env.invalidate_all()
            rec2.write({'line_ids': [Command.set(lines.ids)]})
        self.assertEqual(rec2.line_ids, lines)