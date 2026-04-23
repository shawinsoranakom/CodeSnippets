def _generate_sequence_examples(self, annotation_file, excluded_file,
                                  label_map, seconds_per_sequence,
                                  hop_between_sequences,
                                  video_path_format_string):
    """For each row in the annotation CSV, generates corresponding examples.

    When iterating through frames for a single sequence example, skips over
    excluded frames. When moving to the next sequence example, also skips over
    excluded frames as if they don't exist. Generates equal-length sequence
    examples, each with length seconds_per_sequence (1 fps) and gaps of
    hop_between_sequences frames (and seconds) between them, possible greater
    due to excluded frames.

    Args:
      annotation_file: path to the file of AVA CSV annotations.
      excluded_file: path to a CSV file of excluded timestamps for each video.
      label_map: an {int: string} label map.
      seconds_per_sequence: The number of seconds per example in each example.
      hop_between_sequences: The hop between sequences. If less than
          seconds_per_sequence, will overlap.
      video_path_format_string: File path format to glob video files.

    Yields:
      Each prepared tf.SequenceExample of metadata also containing video frames
    """
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
      # for each video, find aggregates near each sampled frame.:
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
        while middle_frame_time < POSSIBLE_TIMESTAMPS[-1]:
          start_time = middle_frame_time - seconds_per_sequence // 2 - (
              0 if seconds_per_sequence % 2 == 0 else 1)
          end_time = middle_frame_time + (seconds_per_sequence // 2)

          total_boxes = []
          total_labels = []
          total_label_strings = []
          total_images = []
          total_source_ids = []
          total_confidences = []
          total_is_annotated = []
          windowed_timestamp = start_time

          while windowed_timestamp < end_time:
            if (media_id, windowed_timestamp) in frame_excluded:
              end_time += 1
              windowed_timestamp += 1
              logging.info('Ignoring and skipping excluded frame.')
              continue

            cur_vid.set(cv2.CAP_PROP_POS_MSEC,
                        (windowed_timestamp) * SECONDS_TO_MILLI)
            _, image = cur_vid.read()
            _, buffer = cv2.imencode('.jpg', image)

            bufstring = buffer.tostring()
            total_images.append(bufstring)
            source_id = str(windowed_timestamp) + '_' + media_id
            total_source_ids.append(source_id)
            total_is_annotated.append(1)

            boxes = []
            labels = []
            label_strings = []
            confidences = []
            for row in frame_annotations[(media_id, windowed_timestamp)]:
              if len(row) > 2 and int(row['action_label']) in label_map:
                boxes.append([float(row['ymin']), float(row['xmin']),
                              float(row['ymax']), float(row['xmax'])])
                labels.append(int(row['action_label']))
                label_strings.append(label_map[int(row['action_label'])])
                confidences.append(1)
              else:
                logging.warning('Unknown label: %s', row['action_label'])

            total_boxes.append(boxes)
            total_labels.append(labels)
            total_label_strings.append(label_strings)
            total_confidences.append(confidences)
            windowed_timestamp += 1

          if total_boxes:
            yield seq_example_util.make_sequence_example(
                'AVA', media_id, total_images, int(height), int(width), 'jpeg',
                total_source_ids, None, total_is_annotated, total_boxes,
                total_label_strings, use_strs_for_source_id=True)

          # Move middle_time_frame, skipping excluded frames
          frames_mv = 0
          frames_excluded_count = 0
          while (frames_mv < hop_between_sequences + frames_excluded_count
                 and middle_frame_time + frames_mv < POSSIBLE_TIMESTAMPS[-1]):
            frames_mv += 1
            if (media_id, windowed_timestamp + frames_mv) in frame_excluded:
              frames_excluded_count += 1
          middle_frame_time += frames_mv

        cur_vid.release()