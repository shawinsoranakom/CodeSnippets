def test_target_model_len_zero(self):
        """
        Saving a model with a GenericForeignKey to a model instance whose
        __len__ method returns 0 (Team.__len__() here) shouldn't fail (#13085).
        """
        team1 = Team.objects.create(name="Backend devs")
        note = Note(note="Deserve a bonus", content_object=team1)
        note.save()