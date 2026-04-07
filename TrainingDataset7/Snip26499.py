def test_set_messages_success_on_delete(self):
        object_to_delete = SomeObject.objects.create(name="MyObject")
        delete_url = reverse("success_msg_on_delete", args=[object_to_delete.pk])
        response = self.client.post(delete_url, follow=True)
        self.assertContains(response, DeleteFormViewWithMsg.success_message)