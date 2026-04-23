def outer_func():
    # These closures share the names and bodies of the functions in the outer
    # scope, but they should have their own independent caches.
    @st.cache(suppress_st_warning=True)
    def cached1():
        st.text("cached function called")
        return "cached value"

    @st.cache(suppress_st_warning=True)
    def cached2():
        st.text("cached function called")
        return "cached value"

    cached1()
    cached2()