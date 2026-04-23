def raise_error(apps, schema_editor):
    # Test atomic operation in non-atomic migration is wrapped in transaction
    Editor = apps.get_model("migrations", "Editor")
    Editor.objects.create(name="Test Editor")
    raise RuntimeError("Abort migration")