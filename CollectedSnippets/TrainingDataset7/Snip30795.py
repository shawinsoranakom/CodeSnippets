def setUpTestData(cls):
        objectas = []
        objectbs = []
        objectcs = []
        a_info = ["one", "two", "three"]
        for name in a_info:
            o = ObjectA(name=name)
            o.save()
            objectas.append(o)
        b_info = [
            ("un", 1, objectas[0]),
            ("deux", 2, objectas[0]),
            ("trois", 3, objectas[2]),
        ]
        for name, number, objecta in b_info:
            o = ObjectB(name=name, num=number, objecta=objecta)
            o.save()
            objectbs.append(o)
        c_info = [("ein", objectas[2], objectbs[2]), ("zwei", objectas[1], objectbs[1])]
        for name, objecta, objectb in c_info:
            o = ObjectC(name=name, objecta=objecta, objectb=objectb)
            o.save()
            objectcs.append(o)