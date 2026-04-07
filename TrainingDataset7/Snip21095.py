def test_do_nothing(self):
        # Testing DO_NOTHING is a bit harder: It would raise IntegrityError for
        # a normal model, so we connect to pre_delete and set the fk to a known
        # value.
        replacement_r = R.objects.create()

        def check_do_nothing(sender, **kwargs):
            obj = kwargs["instance"]
            obj.donothing_set.update(donothing=replacement_r)

        models.signals.pre_delete.connect(check_do_nothing)
        a = create_a("do_nothing")
        a.donothing.delete()
        a = A.objects.get(pk=a.pk)
        self.assertEqual(replacement_r, a.donothing)
        models.signals.pre_delete.disconnect(check_do_nothing)