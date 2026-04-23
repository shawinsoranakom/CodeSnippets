def test_echo(self, _, echo, echo_index, output_index):
        # The empty lines below are part of the test. Do not remove them.
        with echo():

            st.write("Hello")

            "hi"

            def foo(x):
                y = x + 10

                print(y)

            class MyClass(object):
                def do_x(self):
                    pass

                def do_y(self):
                    pass

        echo_str = """```python

st.write("Hello")

"hi"

def foo(x):
    y = x + 10

    print(y)

class MyClass(object):
    def do_x(self):
        pass

    def do_y(self):
        pass


```"""

        element = self.get_delta_from_queue(echo_index).new_element
        self.assertEqual(echo_str, element.markdown.body)

        element = self.get_delta_from_queue(output_index).new_element
        self.assertEqual("Hello", element.markdown.body)

        self.clear_queue()