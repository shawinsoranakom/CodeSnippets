def on_epoch_begin(self, epoch, logs=None):
        self._ts = time.time()
        self._epoch = epoch
        st.subheader("Epoch %s" % epoch)
        self._epoch_chart = st.line_chart()
        self._epoch_progress = st.info("No stats yet.")
        self._epoch_summary = st.empty()