def m2m_create(pk, klass, data):
    instance = klass(id=pk)
    models.Model.save_base(instance, raw=True)
    instance.data.set_base(data, raw=True)
    return [instance]