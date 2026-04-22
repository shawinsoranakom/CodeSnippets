def cached(irrelevant):
    options = ["foo", "bar", "baz"]
    if st.checkbox("custom filters"):
        selected = st.multiselect("filters", options)
    else:
        selected = ["foo"]
    return selected