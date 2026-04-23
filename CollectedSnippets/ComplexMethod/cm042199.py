def _make_commit(self):
    all_dirs, all_files = [], []
    for root, dirs, files in os.walk(self.git_remote_dir):
      if ".git" in root:
        continue
      for d in dirs:
        all_dirs.append(os.path.join(root, d))
      for f in files:
        all_files.append(os.path.join(root, f))

    # make a new dir and some new files
    new_dir = os.path.join(self.git_remote_dir, "this_is_a_new_dir")
    os.mkdir(new_dir)
    for _ in range(random.randrange(5, 30)):
      for d in (new_dir, random.choice(all_dirs)):
        with tempfile.NamedTemporaryFile(dir=d, delete=False) as f:
          f.write(os.urandom(random.randrange(1, 1000000)))

    # modify some files
    for f in random.sample(all_files, random.randrange(5, 50)):
      with open(f, "w+") as ff:
        txt = ff.readlines()
        ff.seek(0)
        for line in txt:
          ff.write(line[::-1])

    # remove some files
    for f in random.sample(all_files, random.randrange(5, 50)):
      os.remove(f)

    # remove some dirs
    for d in random.sample(all_dirs, random.randrange(1, 10)):
      shutil.rmtree(d)

    # commit the changes
    self._run([
      "git add -A",
      "git commit -m 'an update'",
    ], cwd=self.git_remote_dir)