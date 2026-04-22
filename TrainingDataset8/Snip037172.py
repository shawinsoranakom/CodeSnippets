def draw_header_test(join_output):
    strings = [
        "# Header header",
        "## Header header",
        "### Header header",
        "#### Header header",
        "##### Header header",
        "###### Header header",
        "Quisque vel blandit mi. Fusce dignissim leo purus, in imperdiet lectus suscipit nec.",
    ]

    if join_output:
        st.write("\n\n".join(strings))
    else:
        for string in strings:
            st.write(string)