def on_epoch_end(self, epoch, logs=None):
        # st.write('**Summary**')
        indices = np.random.choice(len(self._x_test), 36)
        test_data = self._x_test[indices]
        prediction = np.argmax(self.model.predict(test_data), axis=1)
        st.image(1.0 - test_data, caption=prediction)
        summary = "\n".join(
            "%(k)8s : %(v)8.5f" % {"k": k, "v": v} for (k, v) in logs.items()
        )
        st.text(summary)
        self._summary_stats.text(
            "%(epoch)8s :  %(epoch)s\n%(summary)s"
            % {"epoch": epoch, "summary": summary}
        )