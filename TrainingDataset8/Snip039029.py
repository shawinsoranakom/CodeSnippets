def test_st_pyplot_clear_global_figure(self, _, clear_figure: Optional[bool]):
        """st.pyplot should clear the global figure if `clear_figure` is
        True *or* None.
        """
        plt.hist(np.random.normal(1, 1, size=100), bins=20)
        with patch.object(plt, "clf", wraps=plt.clf, autospec=True) as plt_clf:
            st.pyplot(clear_figure=clear_figure)

            if clear_figure in (True, None):
                plt_clf.assert_called_once()
            else:
                plt_clf.assert_not_called()