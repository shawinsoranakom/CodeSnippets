def test_target_model_bool_false(self):
        """
        Saving a model with a GenericForeignKey to a model instance whose
        __bool__ method returns False (Guild.__bool__() here) shouldn't fail
        (#13085).
        """
        g1 = Guild.objects.create(name="First guild")
        note = Note(note="Note for guild", content_object=g1)
        note.save()