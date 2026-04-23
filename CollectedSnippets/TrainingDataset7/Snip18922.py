def test_ticket_20278(self):
        sr = SelfRef.objects.create()
        with self.assertRaises(ObjectDoesNotExist):
            SelfRef.objects.get(selfref=sr)