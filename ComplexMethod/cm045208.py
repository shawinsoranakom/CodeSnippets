def get_relevant_memos(self, topics: List[str]) -> List[Memo]:
        """
        Returns any memos from the memory bank that appear sufficiently relevant to the input topics.
        """
        self.logger.enter_function()

        # Retrieve all topic matches, and gather them into a single list.
        matches: List[Tuple[str, str, float]] = []  # Each match is a tuple: (topic, memo_id, distance)
        for topic in topics:
            matches.extend(self.string_map.get_related_string_pairs(topic, self.n_results, self.distance_threshold))

        # Build a dict of memo-relevance pairs from the matches.
        memo_relevance_dict: Dict[str, float] = {}
        for match in matches:
            relevance = self.relevance_conversion_threshold - match[2]
            memo_id = match[1]
            if memo_id in memo_relevance_dict:
                memo_relevance_dict[memo_id] += relevance
            else:
                memo_relevance_dict[memo_id] = relevance

        # Log the details of all the retrieved memos.
        self.logger.info("\n{} POTENTIALLY RELEVANT MEMOS".format(len(memo_relevance_dict)))
        for memo_id, relevance in memo_relevance_dict.items():
            memo = self.uid_memo_dict[memo_id]
            details = ""
            if memo.task is not None:
                details += "\n  TASK: {}\n".format(memo.task)
            details += "\n  INSIGHT: {}\n\n  RELEVANCE: {:.3f}\n".format(memo.insight, relevance)
            self.logger.info(details)

        # Sort the memo-relevance pairs by relevance, in descending order.
        memo_relevance_dict = dict(sorted(memo_relevance_dict.items(), key=lambda item: item[1], reverse=True))

        # Compose the list of sufficiently relevant memos to return.
        memo_list: List[Memo] = []
        for memo_id in memo_relevance_dict:
            if memo_relevance_dict[memo_id] >= 0:
                memo_list.append(self.uid_memo_dict[memo_id])

        self.logger.leave_function()
        return memo_list