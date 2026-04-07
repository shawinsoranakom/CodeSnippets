def test_can_reference_existent(self):
        obj = Object.objects.create()
        ref = ObjectReference.objects.create(obj=obj)
        self.assertEqual(ref.obj, obj)

        ref = ObjectReference.objects.get(obj=obj)
        self.assertEqual(ref.obj, obj)