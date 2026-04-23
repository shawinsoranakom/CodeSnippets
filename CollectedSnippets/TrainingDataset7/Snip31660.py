def generic_create(pk, klass, data):
    instance = klass(id=pk)
    instance.data = data[0]
    models.Model.save_base(instance, raw=True)
    for tag in data[1:]:
        instance.tags.create(data=tag)
    return [instance]