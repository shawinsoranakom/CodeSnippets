def _process_response(res: dict, as_string: bool) -> str:
        """Process response from SerpAPI."""
        # logger.debug(res)
        focus = ["title", "snippet", "link"]
        get_focused = lambda x: {i: j for i, j in x.items() if i in focus}

        if "error" in res.keys():
            if res["error"] == "Google hasn't returned any results for this query.":
                toret = "No good search result found"
            else:
                raise ValueError(f"Got error from SerpAPI: {res['error']}")
        elif "answer_box" in res.keys() and "answer" in res["answer_box"].keys():
            toret = res["answer_box"]["answer"]
        elif "answer_box" in res.keys() and "snippet" in res["answer_box"].keys():
            toret = res["answer_box"]["snippet"]
        elif "answer_box" in res.keys() and "snippet_highlighted_words" in res["answer_box"].keys():
            toret = res["answer_box"]["snippet_highlighted_words"][0]
        elif "sports_results" in res.keys() and "game_spotlight" in res["sports_results"].keys():
            toret = res["sports_results"]["game_spotlight"]
        elif "knowledge_graph" in res.keys() and "description" in res["knowledge_graph"].keys():
            toret = res["knowledge_graph"]["description"]
        elif "snippet" in res["organic_results"][0].keys():
            toret = res["organic_results"][0]["snippet"]
        else:
            toret = "No good search result found"

        toret_l = []
        if "answer_box" in res.keys() and "snippet" in res["answer_box"].keys():
            toret_l += [get_focused(res["answer_box"])]
        if res.get("organic_results"):
            toret_l += [get_focused(i) for i in res.get("organic_results")]

        return str(toret) + "\n" + str(toret_l) if as_string else toret_l