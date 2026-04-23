def create_a(name):
    a = A(name=name)
    for name in (
        "auto",
        "auto_nullable",
        "setvalue",
        "setnull",
        "setdefault",
        "setdefault_none",
        "cascade",
        "cascade_nullable",
        "protect",
        "restrict",
        "donothing",
        "o2o_setnull",
    ):
        r = R.objects.create()
        setattr(a, name, r)
    a.child = RChild.objects.create()
    a.child_setnull = RChild.objects.create()
    a.save()
    return a