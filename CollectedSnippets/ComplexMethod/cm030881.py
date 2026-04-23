def test_compute_files_to_delete(self):
        # See bpo-46063 for background
        wd = tempfile.mkdtemp(prefix='test_logging_')
        self.addCleanup(shutil.rmtree, wd)
        times = []
        dt = datetime.datetime.now()
        for i in range(10):
            times.append(dt.strftime('%Y-%m-%d_%H-%M-%S'))
            dt += datetime.timedelta(seconds=5)
        prefixes = ('a.b', 'a.b.c', 'd.e', 'd.e.f', 'g')
        files = []
        rotators = []
        for prefix in prefixes:
            p = os.path.join(wd, '%s.log' % prefix)
            rotator = logging.handlers.TimedRotatingFileHandler(p, when='s',
                                                                interval=5,
                                                                backupCount=7,
                                                                delay=True)
            rotators.append(rotator)
            if prefix.startswith('a.b'):
                for t in times:
                    files.append('%s.log.%s' % (prefix, t))
            elif prefix.startswith('d.e'):
                def namer(filename):
                    dirname, basename = os.path.split(filename)
                    basename = basename.replace('.log', '') + '.log'
                    return os.path.join(dirname, basename)
                rotator.namer = namer
                for t in times:
                    files.append('%s.%s.log' % (prefix, t))
            elif prefix == 'g':
                def namer(filename):
                    dirname, basename = os.path.split(filename)
                    basename = 'g' + basename[6:] + '.oldlog'
                    return os.path.join(dirname, basename)
                rotator.namer = namer
                for t in times:
                    files.append('g%s.oldlog' % t)
        # Create empty files
        for fn in files:
            p = os.path.join(wd, fn)
            with open(p, 'wb') as f:
                pass
        # Now the checks that only the correct files are offered up for deletion
        for i, prefix in enumerate(prefixes):
            rotator = rotators[i]
            candidates = rotator.getFilesToDelete()
            self.assertEqual(len(candidates), 3, candidates)
            if prefix.startswith('a.b'):
                p = '%s.log.' % prefix
                for c in candidates:
                    d, fn = os.path.split(c)
                    self.assertStartsWith(fn, p)
            elif prefix.startswith('d.e'):
                for c in candidates:
                    d, fn = os.path.split(c)
                    self.assertEndsWith(fn, '.log')
                    self.assertStartsWith(fn, prefix + '.')
                    self.assertTrue(fn[len(prefix) + 2].isdigit())
            elif prefix == 'g':
                for c in candidates:
                    d, fn = os.path.split(c)
                    self.assertEndsWith(fn, '.oldlog')
                    self.assertStartsWith(fn, 'g')
                    self.assertTrue(fn[1].isdigit())