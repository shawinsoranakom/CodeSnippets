def fk_create(pk, klass, data):
    instance = klass(id=pk)
    setattr(instance, "data_id", data)
    models.Model.save_base(instance, raw=True)
    return [instance]