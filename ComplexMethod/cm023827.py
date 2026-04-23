def _compare_records(aldb_rec, dict_rec):
    """Compare a record in the ALDB to the dictionary record."""
    assert aldb_rec.is_in_use == dict_rec["in_use"]
    assert aldb_rec.is_controller == (dict_rec["is_controller"])
    assert not aldb_rec.is_high_water_mark
    assert aldb_rec.group == dict_rec["group"]
    assert aldb_rec.target == Address(dict_rec["target"])
    assert aldb_rec.data1 == dict_rec["data1"]
    assert aldb_rec.data2 == dict_rec["data2"]
    assert aldb_rec.data3 == dict_rec["data3"]