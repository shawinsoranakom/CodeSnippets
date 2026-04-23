def test_deleting_inline_with_protected_delete_does_not_validate(self):
        lotr = Novel.objects.create(name="Lord of the rings")
        chapter = Chapter.objects.create(novel=lotr, name="Many Meetings")
        foot_note = FootNote.objects.create(chapter=chapter, note="yadda yadda")

        change_url = reverse("admin:admin_inlines_novel_change", args=(lotr.id,))
        response = self.client.get(change_url)
        data = {
            "name": lotr.name,
            "chapter_set-TOTAL_FORMS": 1,
            "chapter_set-INITIAL_FORMS": 1,
            "chapter_set-MAX_NUM_FORMS": 1000,
            "_save": "Save",
            "chapter_set-0-id": chapter.id,
            "chapter_set-0-name": chapter.name,
            "chapter_set-0-novel": lotr.id,
            "chapter_set-0-DELETE": "on",
        }
        response = self.client.post(change_url, data)
        self.assertContains(
            response,
            "Deleting chapter %s would require deleting "
            "the following protected related objects: foot note %s"
            % (chapter, foot_note),
        )