def outer():
            @st.cache
            def inner():
                st.text("Inside nested cached func")

            return inner()