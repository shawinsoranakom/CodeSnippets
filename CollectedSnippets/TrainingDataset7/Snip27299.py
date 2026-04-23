def inner_method(models, schema_editor):
            Pony = models.get_model(app_label, "Pony")
            Pony.objects.create(pink=1, weight=3.55)
            Pony.objects.create(weight=5)