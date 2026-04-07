def setUpTestData(cls):
        user = User.objects.create(username="test")
        UserProfile.objects.create(user=user, state="KS", city="Lawrence")
        results = UserStatResult.objects.create(results="first results")
        userstat = UserStat.objects.create(user=user, posts=150, results=results)
        StatDetails.objects.create(base_stats=userstat, comments=259)

        user2 = User.objects.create(username="bob")
        results2 = UserStatResult.objects.create(results="moar results")
        advstat = AdvancedUserStat.objects.create(
            user=user2, posts=200, karma=5, results=results2
        )
        StatDetails.objects.create(base_stats=advstat, comments=250)
        p1 = Parent1(name1="Only Parent1")
        p1.save()
        c1 = Child1(name1="Child1 Parent1", name2="Child1 Parent2", value=1)
        c1.save()
        p2 = Parent2(name2="Child2 Parent2")
        p2.save()
        c2 = Child2(name1="Child2 Parent1", parent2=p2, value=2)
        c2.save()