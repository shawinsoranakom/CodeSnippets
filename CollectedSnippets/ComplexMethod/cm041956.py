def run(self, query: str, profile: str, excluded_version: str = "", verbose: bool = False) -> str:
        """_summary_

        Args:
            query (str): 用当前的reflection作为query去检索过去相似的reflection
            profile (str): _description_

        Returns:
            _type_: _description_
        """
        if not self.engine or len(query) <= 2:  # not "" or not '""'
            logger.warning("engine is None or query too short")
            return ""

        # ablation experiment logic
        if profile == RoleType.WEREWOLF.value:  # role werewolf as baseline, don't use experiences
            logger.warning("Disable werewolves' experiences")
            return ""

        results = self.engine.retrieve(query)

        logger.info(f"retrieve {profile}'s experiences")
        experiences = [res.metadata["obj"] for res in results]

        past_experiences = []  # currently use post-process to filter, and later add `filters` in rag
        for exp in experiences:
            if exp.profile == profile and exp.version != excluded_version:
                past_experiences.append(exp)

        if verbose and results:
            logger.info("past_experiences: {}".format("\n\n".join(past_experiences)))
            distances = results[0].score
            logger.info(f"distances: {distances}")

        template = """
        {
            "Situation __i__": "__situation__"
            ,"Moderator's instruction": "__instruction__"
            ,"Your action or speech during that time": "__response__"
            ,"Reality": "In fact, it turned out the true roles are __game_step__",
            ,"Outcome": "You __outcome__ in the end"
        }
        """
        past_experiences = [
            (
                template.replace("__i__", str(i))
                .replace("__situation__", exp.reflection)
                .replace("__instruction__", exp.instruction)
                .replace("__response__", exp.response)
                .replace("__game_step__", exp.game_setup.replace("0 | Game setup:\n", "").replace("\n", " "))
                .replace("__outcome__", exp.outcome)
            )
            for i, exp in enumerate(past_experiences)
        ]
        logger.info("past_experiences: {}".format("\n".join(past_experiences)))
        logger.info("retrieval done")

        return json.dumps(past_experiences)