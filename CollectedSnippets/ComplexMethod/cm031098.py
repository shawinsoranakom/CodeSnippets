def test_connection_reinit(self):
        with memory_database() as cx:
            cx.text_factory = bytes
            cx.row_factory = sqlite.Row
            cu = cx.cursor()
            cu.execute("create table foo (bar)")
            cu.executemany("insert into foo (bar) values (?)",
                           ((str(v),) for v in range(4)))
            cu.execute("select bar from foo")

            rows = [r for r in cu.fetchmany(2)]
            self.assertTrue(all(isinstance(r, sqlite.Row) for r in rows))
            self.assertEqual([r[0] for r in rows], [b"0", b"1"])

            cx.__init__(":memory:")
            cx.execute("create table foo (bar)")
            cx.executemany("insert into foo (bar) values (?)",
                           ((v,) for v in ("a", "b", "c", "d")))

            # This uses the old database, old row factory, but new text factory
            rows = [r for r in cu.fetchall()]
            self.assertTrue(all(isinstance(r, sqlite.Row) for r in rows))
            self.assertEqual([r[0] for r in rows], ["2", "3"])
            cu.close()