def o2o_create(pk, klass, data):
    instance = klass()
    instance.data_id = data
    models.Model.save_base(instance, raw=True)
    return [instance]