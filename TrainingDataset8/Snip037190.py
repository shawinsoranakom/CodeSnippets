def on_train_begin(self, logs=None):
        st.header("Summary")
        self._summary_chart = st.area_chart()
        self._summary_stats = st.text("%8s :  0" % "epoch")
        st.header("Training Log")