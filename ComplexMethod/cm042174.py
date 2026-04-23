def test_alert_sanity_check(self):
    for event_types in EVENTS.values():
      for event_type, a in event_types.items():
        # TODO: add callback alerts
        if not isinstance(a, Alert):
          continue

        if a.alert_size == AlertSize.none:
          assert len(a.alert_text_1) == 0
          assert len(a.alert_text_2) == 0
        elif a.alert_size == AlertSize.small:
          assert len(a.alert_text_1) > 0
          assert len(a.alert_text_2) == 0
        elif a.alert_size == AlertSize.mid:
          assert len(a.alert_text_1) > 0
          assert len(a.alert_text_2) > 0
        else:
          assert len(a.alert_text_1) > 0

        assert a.duration >= 0.

        if event_type not in (ET.WARNING, ET.PERMANENT, ET.PRE_ENABLE):
          assert a.creation_delay == 0.