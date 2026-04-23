def setUpTestData(cls):
        cls.notes = [Note.objects.create(note=str(i), misc=str(i)) for i in range(10)]