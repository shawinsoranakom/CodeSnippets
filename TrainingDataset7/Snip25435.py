def test_on_delete_python_db_variants(self):
        class Artist(models.Model):
            pass

        class Album(models.Model):
            artist = models.ForeignKey(Artist, models.CASCADE)

        class Song(models.Model):
            album = models.ForeignKey(Album, models.RESTRICT)
            artist = models.ForeignKey(Artist, models.DB_CASCADE)

        self.assertEqual(
            Song.check(databases=self.databases),
            [
                Error(
                    "The model cannot have related fields with both database-level and "
                    "Python-level on_delete variants.",
                    obj=Song,
                    id="models.E050",
                ),
            ],
        )