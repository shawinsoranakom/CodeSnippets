def test_inlineformset_factory_with_null_fk(self):
        # inlineformset_factory tests with fk having null=True. see #9462.
        # create some data that will exhibit the issue
        team = Team.objects.create(name="Red Vipers")
        Player(name="Timmy").save()
        Player(name="Bobby", team=team).save()

        PlayerInlineFormSet = inlineformset_factory(Team, Player, fields="__all__")
        formset = PlayerInlineFormSet()
        self.assertQuerySetEqual(formset.get_queryset(), [])

        formset = PlayerInlineFormSet(instance=team)
        players = formset.get_queryset()
        self.assertEqual(len(players), 1)
        (player1,) = players
        self.assertEqual(player1.team, team)
        self.assertEqual(player1.name, "Bobby")