def test_register_model_class_senders_immediately(self):
        """
        Model signals registered with model classes as senders don't use the
        Apps.lazy_model_operation() mechanism.
        """
        # Book isn't registered with apps2, so it will linger in
        # apps2._pending_operations if ModelSignal does the wrong thing.
        apps2 = Apps()
        signals.post_init.connect(self.receiver, sender=Book, apps=apps2)
        self.assertEqual(list(apps2._pending_operations), [])