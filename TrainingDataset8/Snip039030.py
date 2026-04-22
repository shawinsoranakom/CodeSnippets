def test_st_pyplot_clear_figure(self, _, clear_figure: Optional[bool]):
        """st.pyplot should clear the passed-in figure if `clear_figure` is True."""
        fig = plt.figure()
        ax1 = fig.add_subplot(111)
        ax1.hist(np.random.normal(1, 1, size=100), bins=20)
        with patch.object(fig, "clf", wraps=fig.clf, autospec=True) as fig_clf:
            st.pyplot(fig, clear_figure=clear_figure)

            if clear_figure is True:
                fig_clf.assert_called_once()
            else:
                fig_clf.assert_not_called()