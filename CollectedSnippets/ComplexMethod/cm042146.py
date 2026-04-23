def test_avg_frequency_checks(self):
    for poll in (True, False):
      sm = messaging.SubMaster(["modelV2", "carParams", "carState", "cameraOdometry", "liveCalibration"],
                               poll=("modelV2" if poll else None),
                               frequency=(20. if not poll else None))

      checks = {
        "carState": (20, 20),
        "modelV2": (20, 20 if poll else 10),
        "cameraOdometry": (20, 10),
        "liveCalibration": (4, 4),
        "carParams": (None, None),
        "userBookmark": (None, None),
      }

      for service, (max_freq, min_freq) in checks.items():
        if max_freq is not None:
          assert sm._check_avg_freq(service)
          assert sm.freq_tracker[service].max_freq == max_freq*1.2
          assert sm.freq_tracker[service].min_freq == min_freq*0.8
        else:
          assert not sm._check_avg_freq(service)