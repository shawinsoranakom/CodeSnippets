def outer():
                @cache_decorator
                def inner():
                    st.text("Inside nested cached func")

                return inner()