def test_instance_update(self):
        deleted = []
        related_setnull_sets = []

        def pre_delete(sender, **kwargs):
            obj = kwargs["instance"]
            deleted.append(obj)
            if isinstance(obj, R):
                related_setnull_sets.append([a.pk for a in obj.setnull_set.all()])

        models.signals.pre_delete.connect(pre_delete)
        a = create_a("update_setnull")
        a.setnull.delete()

        a = create_a("update_cascade")
        a.cascade.delete()

        for obj in deleted:
            self.assertIsNone(obj.pk)

        for pk_list in related_setnull_sets:
            for a in A.objects.filter(id__in=pk_list):
                self.assertIsNone(a.setnull)

        models.signals.pre_delete.disconnect(pre_delete)