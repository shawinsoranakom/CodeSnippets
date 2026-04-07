def test_no_deletion(self):
        inline = MediaPermanentInline(EpisodePermanent, admin_site)
        fake_request = object()
        formset = inline.get_formset(fake_request)
        self.assertFalse(formset.can_delete)