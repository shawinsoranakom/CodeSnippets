def test_compute_files_to_delete_same_filename_different_extensions(self):
        # See GH-93205 for background
        wd = pathlib.Path(tempfile.mkdtemp(prefix='test_logging_'))
        self.addCleanup(shutil.rmtree, wd)
        times = []
        dt = datetime.datetime.now()
        n_files = 10
        for _ in range(n_files):
            times.append(dt.strftime('%Y-%m-%d_%H-%M-%S'))
            dt += datetime.timedelta(seconds=5)
        prefixes = ('a.log', 'a.log.b')
        files = []
        rotators = []
        for i, prefix in enumerate(prefixes):
            backupCount = i+1
            rotator = logging.handlers.TimedRotatingFileHandler(wd / prefix, when='s',
                                                                interval=5,
                                                                backupCount=backupCount,
                                                                delay=True)
            rotators.append(rotator)
            for t in times:
                files.append('%s.%s' % (prefix, t))
        for t in times:
            files.append('a.log.%s.c' % t)
        # Create empty files
        for f in files:
            (wd / f).touch()
        # Now the checks that only the correct files are offered up for deletion
        for i, prefix in enumerate(prefixes):
            backupCount = i+1
            rotator = rotators[i]
            candidates = rotator.getFilesToDelete()
            self.assertEqual(len(candidates), n_files - backupCount, candidates)
            matcher = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\z")
            for c in candidates:
                d, fn = os.path.split(c)
                self.assertStartsWith(fn, prefix+'.')
                suffix = fn[(len(prefix)+1):]
                self.assertRegex(suffix, matcher)