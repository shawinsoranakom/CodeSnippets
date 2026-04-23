def test_exclude_reverse_fk_field_ref(self):
        tag = Tag.objects.create()
        Note.objects.create(tag=tag, note="note")
        annotation = Annotation.objects.create(name="annotation", tag=tag)
        self.assertEqual(
            Annotation.objects.exclude(tag__note__note=F("name")).get(), annotation
        )