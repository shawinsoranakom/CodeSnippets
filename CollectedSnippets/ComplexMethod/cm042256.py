def test_sometimes_transparent_commuter(self):
    _visible_time = np.random.choice([0.5, 10])
    ds_vector = always_no_face[:]*2
    interaction_vector = always_false[:]*2
    ds_vector[int((2*INVISIBLE_SECONDS_TO_ORANGE+1)/DT_DMON):int((2*INVISIBLE_SECONDS_TO_ORANGE+1+_visible_time)/DT_DMON)] = \
                                                                                             [msg_ATTENTIVE] * int(_visible_time/DT_DMON)
    interaction_vector[int((INVISIBLE_SECONDS_TO_ORANGE)/DT_DMON):int((INVISIBLE_SECONDS_TO_ORANGE+1)/DT_DMON)] = [True] * int(1/DT_DMON)
    alert_lvls, _ = self._run_seq(ds_vector, interaction_vector, 2*always_true, 2*always_false)
    assert alert_lvls[int(INVISIBLE_SECONDS_TO_ORANGE*0.5/DT_DMON)] == 0
    assert alert_lvls[int((INVISIBLE_SECONDS_TO_ORANGE-0.1)/DT_DMON)] == 2
    assert alert_lvls[int((INVISIBLE_SECONDS_TO_ORANGE+0.1)/DT_DMON)] == 0
    if _visible_time == 0.5:
      assert alert_lvls[int((INVISIBLE_SECONDS_TO_ORANGE*2+1-0.1)/DT_DMON)] == 2
      assert alert_lvls[int((INVISIBLE_SECONDS_TO_ORANGE*2+1+0.1+_visible_time)/DT_DMON)] == 1
    elif _visible_time == 10:
      assert alert_lvls[int((INVISIBLE_SECONDS_TO_ORANGE*2+1-0.1)/DT_DMON)] == 2
      assert alert_lvls[int((INVISIBLE_SECONDS_TO_ORANGE*2+1+0.1+_visible_time)/DT_DMON)] == 0