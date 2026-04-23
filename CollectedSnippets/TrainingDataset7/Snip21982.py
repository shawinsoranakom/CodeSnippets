def test_not_a_directory(self):
        default_storage.delete(UPLOAD_TO)
        # Create a file with the upload directory name
        with SimpleUploadedFile(UPLOAD_TO, b"x") as file:
            default_storage.save(UPLOAD_FOLDER, file)
        self.addCleanup(default_storage.delete, UPLOAD_TO)
        msg = "%s exists and is not a directory." % UPLOAD_TO
        with self.assertRaisesMessage(FileExistsError, msg):
            with SimpleUploadedFile("foo.txt", b"x") as file:
                self.obj.testfile.save("foo.txt", file, save=False)