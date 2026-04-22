def test_sympy_expression(self):
        try:
            import sympy

            a, b = sympy.symbols("a b")
            out = a + b
        except:
            out = "a + b"

        st.latex(out)

        c = self.get_delta_from_queue().new_element.markdown
        self.assertEqual(c.body, "$$\na + b\n$$")