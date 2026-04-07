def test_correct_extraction_psycopg_version(self):
        from django.db.backends.postgresql.base import Database, psycopg_version

        psycopg_version.cache_clear()
        with mock.patch.object(Database, "__version__", "4.2.1 (dt dec pq3 ext lo64)"):
            self.addCleanup(psycopg_version.cache_clear)
            self.assertEqual(psycopg_version(), (4, 2, 1))
        psycopg_version.cache_clear()
        with mock.patch.object(
            Database, "__version__", "4.2b0.dev1 (dt dec pq3 ext lo64)"
        ):
            self.assertEqual(psycopg_version(), (4, 2))