def pre_delete(sender, **kwargs):
            obj = kwargs["instance"]
            deleted.append(obj)
            if isinstance(obj, R):
                related_setnull_sets.append([a.pk for a in obj.setnull_set.all()])