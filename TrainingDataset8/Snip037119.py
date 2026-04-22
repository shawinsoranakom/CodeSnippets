def foo():
    side_effects.append("function ran")
    r = st.radio("radio", ["foo", "bar", "baz", "qux"], index=1)
    return r