def prevent_deletes(sender, instance, **kwargs):
    raise models.ProtectedError("Not allowed to delete.", [instance])