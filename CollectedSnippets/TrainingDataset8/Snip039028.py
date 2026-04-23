def test_st_pyplot(self):
        """Test st.pyplot.

        Need to test:
        * Failed import of matplotlib.
        * Passing in a figure.
        """

        # Make this deterministic
        np.random.seed(19680801)
        data = np.random.randn(2, 20)

        # Generate a 2 inch x 2 inch figure
        fig, ax = plt.subplots(figsize=(2, 2))
        # Add 20 random points to scatter plot.
        ax.scatter(data[0], data[1])

        st.pyplot(fig)

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.imgs.width, -2)
        self.assertEqual(el.imgs.imgs[0].caption, "")
        self.assertTrue(el.imgs.imgs[0].url.startswith(MEDIA_ENDPOINT))