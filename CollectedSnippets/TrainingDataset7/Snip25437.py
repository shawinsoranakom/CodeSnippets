def test_on_delete_db_do_nothing(self):
        class Artist(models.Model):
            pass

        class Album(models.Model):
            artist = models.ForeignKey(Artist, models.CASCADE)

        class Song(models.Model):
            album = models.ForeignKey(Album, models.DO_NOTHING)
            artist = models.ForeignKey(Artist, models.DB_CASCADE)

        self.assertEqual(Song.check(databases=self.databases), [])