def test_latex(self):
        st.latex("ax^2 + bx + c = 0")

        c = self.get_delta_from_queue().new_element.markdown
        self.assertEqual(c.body, "$$\nax^2 + bx + c = 0\n$$")