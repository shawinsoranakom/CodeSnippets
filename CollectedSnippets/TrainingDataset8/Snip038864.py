def test_verify_np_shape(self):
        """Test streamlit.image.verify_np_shape.
        Need to test the following:
        * check shape not (2, 3)
        * check shape 3 but dims 1, 3, 4
        * if only one channel convert to just 2 dimensions.
        """
        with pytest.raises(StreamlitAPIException) as shape_exc:
            st.image(np.ndarray(shape=1))
        self.assertEqual(
            "Numpy shape has to be of length 2 or 3.", str(shape_exc.value)
        )

        with pytest.raises(StreamlitAPIException) as shape2_exc:
            st.image(np.ndarray(shape=(1, 2, 2)))
        self.assertEqual(
            "Channel can only be 1, 3, or 4 got 2. Shape is (1, 2, 2)",
            str(shape2_exc.value),
        )