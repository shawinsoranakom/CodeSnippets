def main():
    with st.session_state.news_container.container():
        st.markdown(
            " <style> div[class^='block-container'] { padding-top: 1rem; } h1 { margin-bottom: -10px; } </style> "
            "<h1 style='text-align: center;'>Headlines and Stories</h1> ",
            unsafe_allow_html=True,
        )
        if st.session_state.news is not None:
            story = -1
            expanded = False
            for i in st.session_state.news.index:
                story += 1
                expanded = story == 0
                text = (
                    st.session_state.news.loc[i].text
                    if "text" in st.session_state.news.loc[i]
                    else st.session_state.news.loc[i].get("title")
                )
                src = st.session_state.news.loc[i].url
                date = str(st.session_state.news.loc[i].date)
                title = st.session_state.news.loc[i].title
                if text and text is not nan and text != "":
                    with st.expander(label=f"{date}  -  {title}", expanded=expanded):
                        st.markdown(
                            f"""
                        <div style='max-width: 90%; margin: auto; word-wrap: break-word;'>
                            <h2 style='text-align: center;'>{title}</h2>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                        if st.session_state.selected_provider == "Benzinga":
                            _tags = (
                                st.session_state.news.loc[i].tags
                                if st.session_state.news.loc[i].get("tags")
                                else ""
                            )
                            _stocks = (
                                st.session_state.news.loc[i].stocks
                                if st.session_state.news.loc[i].get("stocks")
                                else ""
                            )
                            _channels = (
                                st.session_state.news.loc[i].channels
                                if st.session_state.news.loc[i].get("channels")
                                else ""
                            )
                            _images = (
                                st.session_state.news.loc[i].images
                                if st.session_state.news.loc[i].get("images")
                                else []
                            )
                            _url = st.session_state.news.loc[i].url
                            st.markdown(
                                """
                            <style>
                            img {
                                max-width: 98%;
                                height: auto;
                                margin: auto;
                            }
                            </style>
                            """,
                                unsafe_allow_html=True,
                            )
                            if _images and _images is not nan:
                                img = _images[0].get("url")
                                if img is not None:
                                    st.markdown(
                                        f"<div style='text-align: center;'><img src='{img}'></div><br></br>",
                                        unsafe_allow_html=True,
                                    )
                            if text is not None:
                                st.markdown(text, unsafe_allow_html=True)
                            st.divider()
                            st.write(_url)
                            if _tags:
                                st.markdown(
                                    f"##### Tags for this story:  \n {_tags}  \n"
                                )
                            if _stocks and _stocks is not nan:
                                st.markdown(f"##### Stocks mentioned:\n {_stocks}  \n")
                            if _channels:
                                st.markdown(
                                    f"##### Channels for this story:  \n {_channels}  \n"
                                )

                        if st.session_state.selected_provider == "Biztoc":
                            if st.session_state.news.loc[i].get("images") not in [
                                None,
                                nan,
                            ]:
                                img = st.session_state.news.loc[i].images[0].get("s")
                                img = (
                                    st.session_state.news.loc[i].images.get("o")
                                    if img is None
                                    else img
                                )
                                if img is not None:
                                    st.markdown(
                                        f"<div style='text-align: center;'><img src='{img}'></div><br></br>",
                                        unsafe_allow_html=True,
                                    )
                            if text:
                                st.markdown(text, unsafe_allow_html=True)
                            st.write(src)
                            _story_tags = st.session_state.news.loc[i].get("tags")
                            _story_tags = ",".join(_story_tags) if _story_tags else ""
                            if _story_tags:
                                st.divider()
                                st.markdown(
                                    f"##### Tags for this story: \n {_story_tags}  \n\n"
                                )

                        if st.session_state.selected_provider == "Intrinio":
                            _tags = st.session_state.news.loc[i].get("tags")
                            _stocks = (
                                st.session_state.news.loc[i]["company"].get("ticker")
                                if st.session_state.news.loc[i].get("company")
                                else None
                            )
                            _images = st.session_state.news.loc[i].get("images")
                            _url = st.session_state.news.loc[i].get("url")
                            st.markdown(text, unsafe_allow_html=True)
                            if _url:
                                st.write(_url)
                            if _stocks and _stocks is not nan:
                                st.divider()
                                st.markdown(f"##### Stocks mentioned:\n {_stocks}  \n")

                        if st.session_state.selected_provider == "FMP":
                            _url = st.session_state.news.loc[i].get("url")
                            _images = st.session_state.news.loc[i].get("images")
                            _symbols = st.session_state.news.loc[i].get("symbols")
                            img = (
                                _images[0].get("o") or _images[0].get("url")
                                if _images
                                else None
                            )
                            if img is not None:
                                st.markdown(
                                    f"""
                                <div style='text-align: center;'>
                                    <img src='{img}' width='95%' />
                                </div>
                                <br>
                                """,
                                    unsafe_allow_html=True,
                                )
                            if text:
                                st.markdown(text, unsafe_allow_html=True)
                            if _url:
                                st.write(_url)

                        if st.session_state.selected_provider == "Tiingo":
                            _url = st.session_state.news.loc[i].get("url")
                            _tags = st.session_state.news.loc[i].get("tags")
                            _stocks = st.session_state.news.loc[i].get("symbols")
                            if _url:
                                st.write(_url)
                            st.divider()
                            if _tags:
                                st.markdown(
                                    f"##### Tags for this story:  \n {_tags}  \n"
                                )
                            if _stocks and _stocks is not nan:
                                st.markdown(f"##### Stocks mentioned:\n {_stocks}  \n")

            st.divider()
        st.write(
            "Learn more about the OpenBB Platform [here](https://docs.openbb.co/platform)"
        )