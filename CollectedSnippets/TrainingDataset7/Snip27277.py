def raise_error(apps, schema_editor):
    # Test operation in non-atomic migration is not wrapped in transaction
    Publisher = apps.get_model("migrations", "Publisher")
    Publisher.objects.create(name="Test Publisher")
    raise RuntimeError("Abort migration")