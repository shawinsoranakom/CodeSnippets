def inherited_create(pk, klass, data):
    instance = klass(id=pk, **data)
    # This isn't a raw save because:
    #  1) we're testing inheritance, not field behavior, so none
    #     of the field values need to be protected.
    #  2) saving the child class and having the parent created
    #     automatically is easier than manually creating both.
    models.Model.save(instance)
    created = [instance]
    for klass in instance._meta.parents:
        created.append(klass.objects.get(id=pk))
    return created