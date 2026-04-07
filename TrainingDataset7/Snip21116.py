def test_deletion_order(self):
        pre_delete_order = []
        post_delete_order = []

        def log_post_delete(sender, **kwargs):
            pre_delete_order.append((sender, kwargs["instance"].pk))

        def log_pre_delete(sender, **kwargs):
            post_delete_order.append((sender, kwargs["instance"].pk))

        models.signals.post_delete.connect(log_post_delete)
        models.signals.pre_delete.connect(log_pre_delete)

        r = R.objects.create()
        s1 = S.objects.create(r=r)
        s2 = S.objects.create(r=r)
        t1 = T.objects.create(s=s1)
        t2 = T.objects.create(s=s2)
        rchild = RChild.objects.create(r_ptr=r)
        r_pk = r.pk
        r.delete()
        self.assertEqual(
            pre_delete_order,
            [
                (T, t2.pk),
                (T, t1.pk),
                (RChild, rchild.pk),
                (S, s2.pk),
                (S, s1.pk),
                (R, r_pk),
            ],
        )
        self.assertEqual(
            post_delete_order,
            [
                (T, t1.pk),
                (T, t2.pk),
                (RChild, rchild.pk),
                (S, s1.pk),
                (S, s2.pk),
                (R, r_pk),
            ],
        )

        models.signals.post_delete.disconnect(log_post_delete)
        models.signals.pre_delete.disconnect(log_pre_delete)