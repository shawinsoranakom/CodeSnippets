def test_runtime_choicefield_populated(self):
        self.maxDiff = None
        # Here, we demonstrate that choices for a ForeignKey ChoiceField are
        # determined at runtime, based on the data in the database when the
        # form is displayed, not the data in the database when the form is
        # instantiated.
        self.create_basic_data()
        f = ArticleForm(auto_id=False)
        self.assertHTMLEqual(
            f.as_ul(),
            '<li>Headline: <input type="text" name="headline" maxlength="50" required>'
            "</li>"
            '<li>Slug: <input type="text" name="slug" maxlength="50" required></li>'
            '<li>Pub date: <input type="text" name="pub_date" required></li>'
            '<li>Writer: <select name="writer" required>'
            '<option value="" selected>---------</option>'
            '<option value="%s">Bob Woodward</option>'
            '<option value="%s">Mike Royko</option>'
            "</select></li>"
            '<li>Article: <textarea rows="10" cols="40" name="article" required>'
            "</textarea></li>"
            '<li>Categories: <select multiple name="categories">'
            '<option value="%s">Entertainment</option>'
            '<option value="%s">It&#x27;s a test</option>'
            '<option value="%s">Third test</option>'
            "</select> </li>"
            '<li>Status: <select name="status">'
            '<option value="" selected>---------</option>'
            '<option value="1">Draft</option>'
            '<option value="2">Pending</option>'
            '<option value="3">Live</option>'
            "</select></li>"
            % (self.w_woodward.pk, self.w_royko.pk, self.c1.pk, self.c2.pk, self.c3.pk),
        )

        c4 = Category.objects.create(name="Fourth", url="4th")
        w_bernstein = Writer.objects.create(name="Carl Bernstein")
        self.assertHTMLEqual(
            f.as_ul(),
            '<li>Headline: <input type="text" name="headline" maxlength="50" required>'
            "</li>"
            '<li>Slug: <input type="text" name="slug" maxlength="50" required></li>'
            '<li>Pub date: <input type="text" name="pub_date" required></li>'
            '<li>Writer: <select name="writer" required>'
            '<option value="" selected>---------</option>'
            '<option value="%s">Bob Woodward</option>'
            '<option value="%s">Carl Bernstein</option>'
            '<option value="%s">Mike Royko</option>'
            "</select></li>"
            '<li>Article: <textarea rows="10" cols="40" name="article" required>'
            "</textarea></li>"
            '<li>Categories: <select multiple name="categories">'
            '<option value="%s">Entertainment</option>'
            '<option value="%s">It&#x27;s a test</option>'
            '<option value="%s">Third test</option>'
            '<option value="%s">Fourth</option>'
            "</select></li>"
            '<li>Status: <select name="status">'
            '<option value="" selected>---------</option>'
            '<option value="1">Draft</option>'
            '<option value="2">Pending</option>'
            '<option value="3">Live</option>'
            "</select></li>"
            % (
                self.w_woodward.pk,
                w_bernstein.pk,
                self.w_royko.pk,
                self.c1.pk,
                self.c2.pk,
                self.c3.pk,
                c4.pk,
            ),
        )