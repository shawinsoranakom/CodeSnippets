def init_game_setup(
        self,
        role_uniq_objs: list[object],
        num_villager: int = 2,
        num_werewolf: int = 2,
        shuffle=True,
        add_human=False,
        use_reflection=True,
        use_experience=False,
        use_memory_selection=False,
        new_experience_version="",
        prepare_human_player=Callable,
    ) -> tuple[str, list]:
        """init players using different roles' num"""
        role_objs = []
        for role_obj in role_uniq_objs:
            if RoleType.VILLAGER.value in str(role_obj):
                role_objs.extend([role_obj] * num_villager)
            elif RoleType.WEREWOLF.value in str(role_obj):
                role_objs.extend([role_obj] * num_werewolf)
            else:
                role_objs.append(role_obj)
        if shuffle:
            random.shuffle(role_objs)
        if add_human:
            assigned_role_idx = random.randint(0, len(role_objs) - 1)
            assigned_role = role_objs[assigned_role_idx]
            role_objs[assigned_role_idx] = prepare_human_player(assigned_role)  # TODO

        players = [
            role(
                name=f"Player{i + 1}",
                use_reflection=use_reflection,
                use_experience=use_experience,
                use_memory_selection=use_memory_selection,
                new_experience_version=new_experience_version,
            )
            for i, role in enumerate(role_objs)
        ]

        if add_human:
            logger.info(f"You are assigned {players[assigned_role_idx].name}({players[assigned_role_idx].profile})")

        game_setup = ["Game setup:"] + [f"{player.name}: {player.profile}," for player in players]
        self.game_setup = "\n".join(game_setup)

        self._init_players_state(players)  # init players state

        return self.game_setup, players