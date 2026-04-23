def test_unique_together_with_inlineformset_factory(self):
        # Also see bug #8882.

        repository = Repository.objects.create(name="Test Repo")
        FormSet = inlineformset_factory(Repository, Revision, extra=1, fields="__all__")
        data = {
            "revision_set-TOTAL_FORMS": "1",
            "revision_set-INITIAL_FORMS": "0",
            "revision_set-MAX_NUM_FORMS": "",
            "revision_set-0-repository": repository.pk,
            "revision_set-0-revision": "146239817507f148d448db38840db7c3cbf47c76",
            "revision_set-0-DELETE": "",
        }
        formset = FormSet(data, instance=repository)
        self.assertTrue(formset.is_valid())
        saved = formset.save()
        self.assertEqual(len(saved), 1)
        (revision1,) = saved
        self.assertEqual(revision1.repository, repository)
        self.assertEqual(revision1.revision, "146239817507f148d448db38840db7c3cbf47c76")

        # attempt to save the same revision against the same repo.
        data = {
            "revision_set-TOTAL_FORMS": "1",
            "revision_set-INITIAL_FORMS": "0",
            "revision_set-MAX_NUM_FORMS": "",
            "revision_set-0-repository": repository.pk,
            "revision_set-0-revision": "146239817507f148d448db38840db7c3cbf47c76",
            "revision_set-0-DELETE": "",
        }
        formset = FormSet(data, instance=repository)
        self.assertFalse(formset.is_valid())
        self.assertEqual(
            formset.errors,
            [
                {
                    "__all__": [
                        "Revision with this Repository and Revision already exists."
                    ]
                }
            ],
        )

        # unique_together with inlineformset_factory with overridden form
        # fields Also see #9494

        FormSet = inlineformset_factory(
            Repository, Revision, fields=("revision",), extra=1
        )
        data = {
            "revision_set-TOTAL_FORMS": "1",
            "revision_set-INITIAL_FORMS": "0",
            "revision_set-MAX_NUM_FORMS": "",
            "revision_set-0-repository": repository.pk,
            "revision_set-0-revision": "146239817507f148d448db38840db7c3cbf47c76",
            "revision_set-0-DELETE": "",
        }
        formset = FormSet(data, instance=repository)
        self.assertFalse(formset.is_valid())