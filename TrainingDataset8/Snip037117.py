def foo(i):
    options = ["foo", "bar", "baz", "qux"]
    r = st.radio("radio", options, index=i)
    return r