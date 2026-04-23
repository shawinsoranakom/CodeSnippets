def run_matrix_multiplcation(
    pairs: list[tuple[np.ndarray, np.ndarray]], dtype: type
) -> None:
    pairs_T = list(zip(*pairs))
    a = [a_i.astype(dtype) for a_i in pairs_T[0]]
    b = [b_i.astype(dtype) for b_i in pairs_T[1]]
    t = table_from_pandas(pd.DataFrame({"a": a, "b": b, "i": list(range(len(a)))}))
    res = t.select(pw.this.i, c=t.a @ t.b)
    res_pd = table_to_pandas(res).sort_values(by="i")["c"]
    expected = [a_i @ b_i for a_i, b_i in zip(a, b)]
    for res_i, exp_i in zip(res_pd, expected):
        if dtype == float:
            assert np.isclose(res_i, exp_i, rtol=1e-15, atol=0.0).all()
        else:
            assert (res_i == exp_i).all()
        assert res_i.shape == exp_i.shape