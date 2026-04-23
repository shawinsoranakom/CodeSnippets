def collect_train_frames(self):
    """Creates a list of training frames."""
    all_frames = []
    for date in self.date_list:
      date_dir = os.path.join(self.dataset_dir, date)
      drive_set = os.listdir(date_dir)
      for dr in drive_set:
        drive_dir = os.path.join(date_dir, dr)
        if os.path.isdir(drive_dir):
          if dr[:-5] in self.test_scenes:
            continue
          for cam in self.cam_ids:
            img_dir = os.path.join(drive_dir, 'image_' + cam, 'data')
            num_frames = len(glob.glob(img_dir + '/*[0-9].png'))
            for i in range(num_frames):
              frame_id = '%.10d' % i
              all_frames.append(dr + ' ' + cam + ' ' + frame_id)

    for s in self.static_frames:
      try:
        all_frames.remove(s)
      except ValueError:
        pass

    self.train_frames = all_frames
    self.num_train = len(self.train_frames)