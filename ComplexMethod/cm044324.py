def fetch_openbb():
    kwargs = {
        "provider": st.session_state.selected_provider.lower(),
        "limit": st.session_state.selected_limit,
    }
    if st.session_state.selected_provider == "Benzinga":
        kwargs["start_date"] = st.session_state.news_start_date.strftime("%Y-%m-%d")
        kwargs["end_date"] = st.session_state.news_end_date.strftime("%Y-%m-%d")
        kwargs["topics"] = st.session_state.selected_tags
        kwargs["display"] = "full"
        kwargs["page_size"] = 100
        kwargs["channels"] = (
            st.session_state.selected_benzinga_channel.lower()
            if st.session_state.selected_benzinga_channel
            else None
        )
        kwargs["symbol"] = (
            st.session_state.benzinga_tickers
            if st.session_state.benzinga_tickers
            else None
        )

    if st.session_state.selected_provider == "Biztoc":
        kwargs["term"] = st.session_state.selected_term
        kwargs["tag"] = st.session_state.selected_tags
        kwargs["filter"] = "tag" if kwargs.get("tag") else None
        if kwargs.get("filter") is None:
            kwargs["filter"] = "latest"
        kwargs["source"] = (
            st.session_state.selected_biztoc_source
            if st.session_state.selected_biztoc_source
            else None
        )
        kwargs["filter"] = "source" if kwargs.get("source") else kwargs.get("filter")
        if kwargs.get("filter") == "source":
            kwargs.pop("tag")

    if st.session_state.selected_provider == "FMP":
        kwargs["symbol"] = (
            st.session_state.fmp_tickers if st.session_state.fmp_tickers else None
        )

    if st.session_state.selected_provider == "Intrinio":
        kwargs["symbol"] = (
            st.session_state.intrinio_tickers
            if st.session_state.intrinio_tickers
            else None
        )

    if st.session_state.selected_provider == "Tiingo":
        kwargs["start_date"] = st.session_state.news_start_date.strftime("%Y-%m-%d")
        kwargs["end_date"] = st.session_state.news_end_date.strftime("%Y-%m-%d")
        kwargs["symbol"] = (
            st.session_state.tiingo_tickers if st.session_state.tiingo_tickers else None
        )

    kwargs = {key: value for key, value in kwargs.items() if value is not None}

    data = (
        obb.news.company(**kwargs)  # type: ignore
        if kwargs.get("symbol")
        else obb.news.world(**kwargs)  # type: ignore
    )
    if data.results != []:
        return data.to_df().sort_index(ascending=False).reset_index()