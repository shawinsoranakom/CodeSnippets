def test_formset_name(self):
        ArticleFormSet = formset_factory(ArticleForm)
        ChoiceFormSet = formset_factory(Choice)
        self.assertEqual(ArticleFormSet.__name__, "ArticleFormSet")
        self.assertEqual(ChoiceFormSet.__name__, "ChoiceFormSet")