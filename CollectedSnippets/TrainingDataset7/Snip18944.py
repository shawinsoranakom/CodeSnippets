def test_select_on_save_lying_update(self):
        """
        select_on_save works correctly if the database doesn't return correct
        information about matched rows from UPDATE.
        """
        # Change the manager to not return "row matched" for update().
        # We are going to change the Article's _base_manager class
        # dynamically. This is a bit of a hack, but it seems hard to
        # test this properly otherwise. Article's manager, because
        # proxy models use their parent model's _base_manager.

        orig_class = Article._base_manager._queryset_class

        class FakeQuerySet(models.QuerySet):
            # Make sure the _update method below is in fact called.
            called = False

            def _update(self, *args, **kwargs):
                FakeQuerySet.called = True
                super()._update(*args, **kwargs)
                return 0

        try:
            Article._base_manager._queryset_class = FakeQuerySet
            asos = ArticleSelectOnSave.objects.create(pub_date=datetime.now())
            with self.assertNumQueries(3):
                asos.save()
                self.assertTrue(FakeQuerySet.called)
            # This is not wanted behavior, but this is how Django has always
            # behaved for databases that do not return correct information
            # about matched rows for UPDATE.
            with self.assertRaisesMessage(
                DatabaseError, "Forced update did not affect any rows."
            ):
                asos.save(force_update=True)
            msg = (
                "An error occurred in the current transaction. You can't "
                "execute queries until the end of the 'atomic' block."
            )
            with self.assertRaisesMessage(DatabaseError, msg) as cm:
                asos.save(update_fields=["pub_date"])
            self.assertIsInstance(cm.exception.__cause__, DatabaseError)
        finally:
            Article._base_manager._queryset_class = orig_class