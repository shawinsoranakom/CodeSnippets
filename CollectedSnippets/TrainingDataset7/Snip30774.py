def setUpTestData(cls):
        Number.objects.create(num=1)
        Number.objects.create(num=2)

        Article.objects.create(name="one", created=datetime.datetime.now())
        Article.objects.create(name="two", created=datetime.datetime.now())
        Article.objects.create(name="three", created=datetime.datetime.now())
        Article.objects.create(name="four", created=datetime.datetime.now())

        food = Food.objects.create(name="spam")
        Eaten.objects.create(meal="spam with eggs", food=food)