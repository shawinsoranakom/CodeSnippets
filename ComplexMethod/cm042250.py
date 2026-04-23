def get_test_cases() -> list[tuple[str, CarTestRoute | None]]:
  # build list of test cases
  test_cases = []
  if not len(INTERNAL_SEG_LIST):
    routes_by_car = defaultdict(set)
    for r in routes:
      routes_by_car[str(r.car_model)].add(r)

    for i, c in enumerate(sorted(PLATFORMS)):
      if i % NUM_JOBS == JOB_ID:
        test_cases.extend(sorted((c, r) for r in routes_by_car.get(c, (None,))))

  else:
    segment_list = read_segment_list(os.path.join(BASEDIR, INTERNAL_SEG_LIST))
    segment_list = random.sample(segment_list, INTERNAL_SEG_CNT or len(segment_list))
    for platform, segment in segment_list:
      platform = MIGRATION.get(platform, platform)
      segment_name = SegmentName(segment)
      test_cases.append((platform, CarTestRoute(segment_name.route_name.canonical_name, platform,
                                                segment=segment_name.segment_num)))
  return test_cases