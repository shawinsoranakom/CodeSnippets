def im2m_create(pk, klass, data):
    instance = klass(id=pk)
    models.Model.save_base(instance, raw=True)
    return [instance]