def im_create(pk, klass, data):
    instance = klass(id=pk)
    instance.right_id = data["right"]
    instance.left_id = data["left"]
    if "extra" in data:
        instance.extra = data["extra"]
    models.Model.save_base(instance, raw=True)
    return [instance]