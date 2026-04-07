def test_unicode_file_name(self):
        open(os.path.join(self.test_dir, "vidéo.txt"), "a").close()
        management.call_command("makemessages", locale=[LOCALE], verbosity=0)