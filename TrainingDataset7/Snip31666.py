def pk_create(pk, klass, data):
    instance = klass()
    instance.data = data
    models.Model.save_base(instance, raw=True)
    return [instance]