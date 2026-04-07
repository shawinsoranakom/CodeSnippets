def swap():
            obj_1.name, obj_2.name = obj_2.name, obj_1.name
            obj_1.save()
            obj_2.save()