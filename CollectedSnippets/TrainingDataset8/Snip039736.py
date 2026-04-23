def setUp(self):
        self.patch1 = patch("streamlit.file_util.os.stat")
        self.os_stat = self.patch1.start()