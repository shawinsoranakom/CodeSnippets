def _generate_examples(self, annotation_file, excluded_file, label_map,
                         seconds_per_sequence, hop_between_sequences,
                         video_path_format_string):
    """For each row in the annotation CSV, generates examples.

    When iterating through frames for a single example, skips
    over excluded frames. Generates equal-length sequence examples, each with
    length seconds_per_sequence (1 fps) and gaps of hop_between_sequences
    frames (and seconds) between them, possible greater due to excluded frames.

    Args:
      annotation_file: path to the file of AVA CSV annotations.
      excluded_file: path to a CSV file of excluded timestamps for each video.
      label_map: an {int: string} label map.
      seconds_per_sequence: The number of seconds per example in each example.
      hop_between_sequences: The hop between sequences. If less than
          seconds_per_sequence, will overlap.
      video_path_format_string: File path format to glob video files.

    Yields:
      Each prepared tf.Example of metadata also containing video frames
    """
    del seconds_per_sequence
    del hop_between_sequences
    fieldnames = ['id', 'timestamp_seconds', 'xmin', 'ymin', 'xmax', 'ymax',
                  'action_label']
    frame_excluded = {}
    # create a sparse, nested map of videos and frame indices.
    with open(excluded_file, 'r') as excluded:
      reader = csv.reader(excluded)
      for row in reader:
        frame_excluded[(row[0], int(float(row[1])))] = True
    with open(annotation_file, 'r') as annotations:
      reader = csv.DictReader(annotations, fieldnames)
      frame_annotations = collections.defaultdict(list)
      ids = set()
      # aggreggate by video and timestamp:
      for row in reader:
        ids.add(row['id'])
        key = (row['id'], int(float(row['timestamp_seconds'])))
        frame_annotations[key].append(row)
      # for each video, find aggreggates near each sampled frame.:
      logging.info('Generating metadata...')
      media_num = 1
      for media_id in ids:
        logging.info('%d/%d, ignore warnings.\n', media_num, len(ids))
        media_num += 1

        filepath = glob.glob(
            video_path_format_string.format(media_id) + '*')[0]
        cur_vid = cv2.VideoCapture(filepath)
        width = cur_vid.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = cur_vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
        middle_frame_time = POSSIBLE_TIMESTAMPS[0]
        total_non_excluded = 0
        while middle_frame_time < POSSIBLE_TIMESTAMPS[-1]:
          if (media_id, middle_frame_time) not in frame_excluded:
            total_non_excluded += 1
          middle_frame_time += 1

        middle_frame_time = POSSIBLE_TIMESTAMPS[0]
        cur_frame_num = 0
        while middle_frame_time < POSSIBLE_TIMESTAMPS[-1]:
          cur_vid.set(cv2.CAP_PROP_POS_MSEC,
                      middle_frame_time * SECONDS_TO_MILLI)
          _, image = cur_vid.read()
          _, buffer = cv2.imencode('.jpg', image)

          bufstring = buffer.tostring()

          if (media_id, middle_frame_time) in frame_excluded:
            middle_frame_time += 1
            logging.info('Ignoring and skipping excluded frame.')
            continue

          cur_frame_num += 1
          source_id = str(middle_frame_time) + '_' + media_id

          xmins = []
          xmaxs = []
          ymins = []
          ymaxs = []
          areas = []
          labels = []
          label_strings = []
          confidences = []
          for row in frame_annotations[(media_id, middle_frame_time)]:
            if len(row) > 2 and int(row['action_label']) in label_map:
              xmins.append(float(row['xmin']))
              xmaxs.append(float(row['xmax']))
              ymins.append(float(row['ymin']))
              ymaxs.append(float(row['ymax']))
              areas.append(float((xmaxs[-1] - xmins[-1]) *
                                 (ymaxs[-1] - ymins[-1])) / 2)
              labels.append(int(row['action_label']))
              label_strings.append(label_map[int(row['action_label'])])
              confidences.append(1)
            else:
              logging.warning('Unknown label: %s', row['action_label'])

          middle_frame_time += 1/3
          if abs(middle_frame_time - round(middle_frame_time) < 0.0001):
            middle_frame_time = round(middle_frame_time)

          key = hashlib.sha256(bufstring).hexdigest()
          date_captured_feature = (
              '2020-06-17 00:%02d:%02d' % ((middle_frame_time - 900)*3 // 60,
                                           (middle_frame_time - 900)*3 % 60))
          context_feature_dict = {
              'image/height':
                  dataset_util.int64_feature(int(height)),
              'image/width':
                  dataset_util.int64_feature(int(width)),
              'image/format':
                  dataset_util.bytes_feature('jpeg'.encode('utf8')),
              'image/source_id':
                  dataset_util.bytes_feature(source_id.encode('utf8')),
              'image/filename':
                  dataset_util.bytes_feature(source_id.encode('utf8')),
              'image/encoded':
                  dataset_util.bytes_feature(bufstring),
              'image/key/sha256':
                  dataset_util.bytes_feature(key.encode('utf8')),
              'image/object/bbox/xmin':
                  dataset_util.float_list_feature(xmins),
              'image/object/bbox/xmax':
                  dataset_util.float_list_feature(xmaxs),
              'image/object/bbox/ymin':
                  dataset_util.float_list_feature(ymins),
              'image/object/bbox/ymax':
                  dataset_util.float_list_feature(ymaxs),
              'image/object/area':
                  dataset_util.float_list_feature(areas),
              'image/object/class/label':
                  dataset_util.int64_list_feature(labels),
              'image/object/class/text':
                  dataset_util.bytes_list_feature(label_strings),
              'image/location':
                  dataset_util.bytes_feature(media_id.encode('utf8')),
              'image/date_captured':
                  dataset_util.bytes_feature(
                      date_captured_feature.encode('utf8')),
              'image/seq_num_frames':
                  dataset_util.int64_feature(total_non_excluded),
              'image/seq_frame_num':
                  dataset_util.int64_feature(cur_frame_num),
              'image/seq_id':
                  dataset_util.bytes_feature(media_id.encode('utf8')),
          }

          yield tf.train.Example(
              features=tf.train.Features(feature=context_feature_dict))

        cur_vid.release()