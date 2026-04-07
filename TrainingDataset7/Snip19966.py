def test_invalid_uuid_pk_raises_404(self):
        content_type = ContentType.objects.get_for_model(UUIDModel)
        invalid_uuid = "1234-zzzz-5678-0000-invaliduuid"
        with self.assertRaisesMessage(
            Http404,
            f"Content type {content_type.id} object {invalid_uuid} doesn’t exist",
        ):
            shortcut(self.request, content_type.id, invalid_uuid)