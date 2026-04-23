def setUp(self):
        if os.path.exists(temp_storage_dir):
            shutil.rmtree(temp_storage_dir)
        os.mkdir(temp_storage_dir)
        self.addCleanup(shutil.rmtree, temp_storage_dir)