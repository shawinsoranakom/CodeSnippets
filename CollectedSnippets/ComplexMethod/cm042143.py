def _vote_rate_players(self, text: str):
        """
        # calculate the rate of goodteam vote werewolves
        :example:

        input:
        ['Player1', 'Player2', 'Player3', 'Player5', 'Player6']. Say ONLY: I vote to eliminate ...
        Player1(Witch): 49 | I vote to eliminate Player5
        Player2(Villager): 49 | I vote to eliminate Player5
        Player3(Villager): 49 | I vote to eliminate Player5
        Player5(Werewolf): 49 | I vote to eliminate Player6
        Player6(Seer): 49 | I vote to eliminate Player5

        output:
        werewolves:  ['Player5']
        non_werewolves: ['Player1', 'Player2', 'Player3', 'Player6']
        as you can see :Player2(Villager) and   Player3(Villager) vote to eliminate Player5(Werewolf)
        :return goodteam vote rateability: 100.00%
        """
        pattern = re.compile(r"(\w+)\(([^\)]+)\): \d+ \| I vote to eliminate (\w+)")
        # find all werewolves
        werewolves = []
        for match in pattern.finditer(text):
            if match.group(2) == RoleType.WEREWOLF.value:
                werewolves.append(match.group(1))

        # find all non_werewolves
        non_werewolves = []
        for match in pattern.finditer(text):
            if match.group(2) != RoleType.WEREWOLF.value:
                non_werewolves.append(match.group(1))
        num_non_werewolves = len(non_werewolves)

        # count players other than werewolves made the correct votes
        correct_votes = 0
        for match in pattern.finditer(text):
            if match.group(2) != RoleType.WEREWOLF.value and match.group(3) in werewolves:
                correct_votes += 1

        # cal the rateability of non_werewolves
        rate = correct_votes / num_non_werewolves
        good_vote_rate = round(rate, 2)
        return {"good_vote_rate": good_vote_rate, "werewolves": werewolves, "non_werewolves": non_werewolves}