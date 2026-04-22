def test_cached_st_image_replay(self, _, cache_decorator):
        """Basic sanity check that nothing blows up. This test assumes that
        actual caching/replay functionality are covered by e2e tests that
        can more easily test them.
        """

        @cache_decorator
        def img_fn():
            st.image(create_image(10))

        img_fn()
        img_fn()

        @cache_decorator
        def img_fn_multi():
            st.image([create_image(5), create_image(15), create_image(1)])

        img_fn_multi()
        img_fn_multi()