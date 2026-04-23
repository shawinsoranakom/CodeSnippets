def tearDown(self):
        if os.path.exists(temp_storage_location):
            shutil.rmtree(temp_storage_location)