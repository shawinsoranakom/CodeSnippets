def test_database_arg_save_and_delete(self):
        """
        The pre/post_save signal contains the correct database.
        """
        # Make some signal receivers
        pre_save_receiver = DatabaseReceiver()
        post_save_receiver = DatabaseReceiver()
        pre_delete_receiver = DatabaseReceiver()
        post_delete_receiver = DatabaseReceiver()
        # Make model and connect receivers
        signals.pre_save.connect(sender=Person, receiver=pre_save_receiver)
        signals.post_save.connect(sender=Person, receiver=post_save_receiver)
        signals.pre_delete.connect(sender=Person, receiver=pre_delete_receiver)
        signals.post_delete.connect(sender=Person, receiver=post_delete_receiver)
        p = Person.objects.create(name="Darth Vader")
        # Save and test receivers got calls
        p.save()
        self.assertEqual(pre_save_receiver._database, DEFAULT_DB_ALIAS)
        self.assertEqual(post_save_receiver._database, DEFAULT_DB_ALIAS)
        # Delete, and test
        p.delete()
        self.assertEqual(pre_delete_receiver._database, DEFAULT_DB_ALIAS)
        self.assertEqual(post_delete_receiver._database, DEFAULT_DB_ALIAS)
        # Save again to a different database
        p.save(using="other")
        self.assertEqual(pre_save_receiver._database, "other")
        self.assertEqual(post_save_receiver._database, "other")
        # Delete, and test
        p.delete(using="other")
        self.assertEqual(pre_delete_receiver._database, "other")
        self.assertEqual(post_delete_receiver._database, "other")

        signals.pre_save.disconnect(sender=Person, receiver=pre_save_receiver)
        signals.post_save.disconnect(sender=Person, receiver=post_save_receiver)
        signals.pre_delete.disconnect(sender=Person, receiver=pre_delete_receiver)
        signals.post_delete.disconnect(sender=Person, receiver=post_delete_receiver)