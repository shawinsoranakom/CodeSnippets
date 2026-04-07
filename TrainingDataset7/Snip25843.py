def test_lookup_collision(self):
        """
        Genuine field names don't collide with built-in lookup types
        ('year', 'gt', 'range', 'in' etc.) (#11670).
        """
        # 'gt' is used as a code number for the year, e.g. 111=>2009.
        season_2009 = Season.objects.create(year=2009, gt=111)
        season_2009.games.create(home="Houston Astros", away="St. Louis Cardinals")
        season_2010 = Season.objects.create(year=2010, gt=222)
        season_2010.games.create(home="Houston Astros", away="Chicago Cubs")
        season_2010.games.create(home="Houston Astros", away="Milwaukee Brewers")
        season_2010.games.create(home="Houston Astros", away="St. Louis Cardinals")
        season_2011 = Season.objects.create(year=2011, gt=333)
        season_2011.games.create(home="Houston Astros", away="St. Louis Cardinals")
        season_2011.games.create(home="Houston Astros", away="Milwaukee Brewers")
        hunter_pence = Player.objects.create(name="Hunter Pence")
        hunter_pence.games.set(Game.objects.filter(season__year__in=[2009, 2010]))
        pudge = Player.objects.create(name="Ivan Rodriquez")
        pudge.games.set(Game.objects.filter(season__year=2009))
        pedro_feliz = Player.objects.create(name="Pedro Feliz")
        pedro_feliz.games.set(Game.objects.filter(season__year__in=[2011]))
        johnson = Player.objects.create(name="Johnson")
        johnson.games.set(Game.objects.filter(season__year__in=[2011]))

        # Games in 2010
        self.assertEqual(Game.objects.filter(season__year=2010).count(), 3)
        self.assertEqual(Game.objects.filter(season__year__exact=2010).count(), 3)
        self.assertEqual(Game.objects.filter(season__gt=222).count(), 3)
        self.assertEqual(Game.objects.filter(season__gt__exact=222).count(), 3)

        # Games in 2011
        self.assertEqual(Game.objects.filter(season__year=2011).count(), 2)
        self.assertEqual(Game.objects.filter(season__year__exact=2011).count(), 2)
        self.assertEqual(Game.objects.filter(season__gt=333).count(), 2)
        self.assertEqual(Game.objects.filter(season__gt__exact=333).count(), 2)
        self.assertEqual(Game.objects.filter(season__year__gt=2010).count(), 2)
        self.assertEqual(Game.objects.filter(season__gt__gt=222).count(), 2)

        # Games played in 2010 and 2011
        self.assertEqual(Game.objects.filter(season__year__in=[2010, 2011]).count(), 5)
        self.assertEqual(Game.objects.filter(season__year__gt=2009).count(), 5)
        self.assertEqual(Game.objects.filter(season__gt__in=[222, 333]).count(), 5)
        self.assertEqual(Game.objects.filter(season__gt__gt=111).count(), 5)

        # Players who played in 2009
        self.assertEqual(
            Player.objects.filter(games__season__year=2009).distinct().count(), 2
        )
        self.assertEqual(
            Player.objects.filter(games__season__year__exact=2009).distinct().count(), 2
        )
        self.assertEqual(
            Player.objects.filter(games__season__gt=111).distinct().count(), 2
        )
        self.assertEqual(
            Player.objects.filter(games__season__gt__exact=111).distinct().count(), 2
        )

        # Players who played in 2010
        self.assertEqual(
            Player.objects.filter(games__season__year=2010).distinct().count(), 1
        )
        self.assertEqual(
            Player.objects.filter(games__season__year__exact=2010).distinct().count(), 1
        )
        self.assertEqual(
            Player.objects.filter(games__season__gt=222).distinct().count(), 1
        )
        self.assertEqual(
            Player.objects.filter(games__season__gt__exact=222).distinct().count(), 1
        )

        # Players who played in 2011
        self.assertEqual(
            Player.objects.filter(games__season__year=2011).distinct().count(), 2
        )
        self.assertEqual(
            Player.objects.filter(games__season__year__exact=2011).distinct().count(), 2
        )
        self.assertEqual(
            Player.objects.filter(games__season__gt=333).distinct().count(), 2
        )
        self.assertEqual(
            Player.objects.filter(games__season__year__gt=2010).distinct().count(), 2
        )
        self.assertEqual(
            Player.objects.filter(games__season__gt__gt=222).distinct().count(), 2
        )