def inner_method(models, schema_editor):
            Pony = models.get_model("test_runpythonatomic", "Pony")
            Pony.objects.create(pink=1, weight=3.55)
            raise ValueError("Adrian hates ponies.")