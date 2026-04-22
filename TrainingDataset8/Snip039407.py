def test_cached_st_function_replay(self, _):
        @st.experimental_memo(persist="disk")
        def foo(i):
            st.text(i)
            return i

        foo(1)

        deltas = self.get_all_deltas_from_queue()
        text = [
            element.text.body
            for element in (delta.new_element for delta in deltas)
            if element.WhichOneof("type") == "text"
        ]
        assert text == ["1"]