def data_create(pk, klass, data):
    instance = klass(id=pk)
    instance.data = data
    models.Model.save_base(instance, raw=True)
    return [instance]