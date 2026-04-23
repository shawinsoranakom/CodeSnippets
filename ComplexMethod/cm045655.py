def test_method_call():
    date_str = "2023-03-25 12:05:00.000000001+01:00"
    fmt = "%Y-%m-%d %H:%M:%S.%f%z"
    df = pd.DataFrame(
        {
            "txt": [date_str],
            "ts": [pd.to_datetime(date_str, format=fmt)],
            "td": pd.Timedelta(days=1),
            "i": [42],
            "f": [42.3],
        }
    )
    t = pw.debug.table_from_pandas(df)
    assert repr(t.ts.dt.nanosecond()) == "(<table1>.ts).dt.nanosecond()"
    assert repr(t.ts.dt.microsecond()) == "(<table1>.ts).dt.microsecond()"
    assert repr(t.ts.dt.millisecond()) == "(<table1>.ts).dt.millisecond()"
    assert repr(t.ts.dt.second()) == "(<table1>.ts).dt.second()"
    assert repr(t.ts.dt.minute()) == "(<table1>.ts).dt.minute()"
    assert repr(t.ts.dt.hour()) == "(<table1>.ts).dt.hour()"
    assert repr(t.ts.dt.day()) == "(<table1>.ts).dt.day()"
    assert repr(t.ts.dt.month()) == "(<table1>.ts).dt.month()"
    assert repr(t.ts.dt.year()) == "(<table1>.ts).dt.year()"
    with deprecated_call_here(match="unit"):
        assert repr(t.ts.dt.timestamp()) == "(<table1>.ts).dt.timestamp()"
    assert repr(t.ts.dt.timestamp("s")) == "(<table1>.ts).dt.timestamp('s')"
    assert repr(t.ts.dt.strftime("%m")) == "(<table1>.ts).dt.strftime('%m')"
    assert repr(t.td.dt.nanoseconds()) == "(<table1>.td).dt.nanoseconds()"
    assert repr(t.td.dt.microseconds()) == "(<table1>.td).dt.microseconds()"
    assert repr(t.td.dt.milliseconds()) == "(<table1>.td).dt.milliseconds()"
    assert repr(t.td.dt.seconds()) == "(<table1>.td).dt.seconds()"
    assert repr(t.td.dt.hours()) == "(<table1>.td).dt.hours()"
    assert repr(t.td.dt.days()) == "(<table1>.td).dt.days()"
    assert repr(t.td.dt.weeks()) == "(<table1>.td).dt.weeks()"
    assert repr(t.txt.dt.strptime("%m")) == "(<table1>.txt).dt.strptime('%m')"
    assert repr(t.ts.dt.round("D")) == "(<table1>.ts).dt.round('D')"
    assert repr(t.ts.dt.round(t.td)) == "(<table1>.ts).dt.round(<table1>.td)"
    assert repr(t.ts.dt.floor("D")) == "(<table1>.ts).dt.floor('D')"
    assert repr(t.ts.dt.floor(t.td)) == "(<table1>.ts).dt.floor(<table1>.td)"
    assert repr(t.ts.dt.weekday()) == "(<table1>.ts).dt.weekday()"
    assert repr(t.i.dt.from_timestamp("s")) == "(<table1>.i).dt.from_timestamp('s')"
    assert repr(t.f.dt.from_timestamp("s")) == "(<table1>.f).dt.from_timestamp('s')"