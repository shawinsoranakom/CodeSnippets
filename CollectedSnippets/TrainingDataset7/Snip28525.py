def test_commit_false(self):
        # Test the behavior of commit=False and save_m2m

        author1 = Author.objects.create(name="Charles Baudelaire")
        author2 = Author.objects.create(name="Paul Verlaine")
        author3 = Author.objects.create(name="Walt Whitman")

        meeting = AuthorMeeting.objects.create(created=date.today())
        meeting.authors.set(Author.objects.all())

        # create an Author instance to add to the meeting.

        author4 = Author.objects.create(name="John Steinbeck")

        AuthorMeetingFormSet = modelformset_factory(
            AuthorMeeting, fields="__all__", extra=1, can_delete=True
        )
        data = {
            "form-TOTAL_FORMS": "2",  # the number of forms rendered
            "form-INITIAL_FORMS": "1",  # the number of forms with initial data
            "form-MAX_NUM_FORMS": "",  # the max number of forms
            "form-0-id": str(meeting.id),
            "form-0-name": "2nd Tuesday of the Week Meeting",
            "form-0-authors": [author2.id, author1.id, author3.id, author4.id],
            "form-1-name": "",
            "form-1-authors": "",
            "form-1-DELETE": "",
        }
        formset = AuthorMeetingFormSet(data=data, queryset=AuthorMeeting.objects.all())
        self.assertTrue(formset.is_valid())

        instances = formset.save(commit=False)
        for instance in instances:
            instance.created = date.today()
            instance.save()
        formset.save_m2m()
        self.assertSequenceEqual(
            instances[0].authors.all(),
            [author1, author4, author2, author3],
        )