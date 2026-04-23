async def execute(self, plan: str):
        """
        Args:
            plan: This is a string address of the action we need to execute.
            It comes in the form of "{world}:{sector}:{arena}:{game_objects}".
            It is important that you access this without doing negative
            indexing (e.g., [-1]) because the latter address elements may not be
            present in some cases.
            e.g., "dolores double studio:double studio:bedroom 1:bed"
        """
        roles = self.rc.env.get_roles()
        if "<random>" in plan and self.rc.scratch.planned_path == []:
            self.rc.scratch.act_path_set = False

        # <act_path_set> is set to True if the path is set for the current action.
        # It is False otherwise, and means we need to construct a new path.
        if not self.rc.scratch.act_path_set:
            # <target_tiles> is a list of tile coordinates where the persona may go
            # to execute the current action. The goal is to pick one of them.
            target_tiles = None
            logger.info(f"Role {self.name} plan: {plan}")

            if "<persona>" in plan:
                # Executing persona-persona interaction.
                target_p_tile = roles[plan.split("<persona>")[-1].strip()].scratch.curr_tile
                collision_maze = self.rc.env.observe()["collision_maze"]
                potential_path = path_finder(
                    collision_maze, self.rc.scratch.curr_tile, target_p_tile, collision_block_id
                )
                if len(potential_path) <= 2:
                    target_tiles = [potential_path[0]]
                else:
                    collision_maze = self.rc.env.observe()["collision_maze"]
                    potential_1 = path_finder(
                        collision_maze,
                        self.rc.scratch.curr_tile,
                        potential_path[int(len(potential_path) / 2)],
                        collision_block_id,
                    )

                    potential_2 = path_finder(
                        collision_maze,
                        self.rc.scratch.curr_tile,
                        potential_path[int(len(potential_path) / 2) + 1],
                        collision_block_id,
                    )
                    if len(potential_1) <= len(potential_2):
                        target_tiles = [potential_path[int(len(potential_path) / 2)]]
                    else:
                        target_tiles = [potential_path[int(len(potential_path) / 2 + 1)]]

            elif "<waiting>" in plan:
                # Executing interaction where the persona has decided to wait before
                # executing their action.
                x = int(plan.split()[1])
                y = int(plan.split()[2])
                target_tiles = [[x, y]]

            elif "<random>" in plan:
                # Executing a random location action.
                plan = ":".join(plan.split(":")[:-1])

                address_tiles = self.rc.env.observe()["address_tiles"]
                target_tiles = address_tiles[plan]
                target_tiles = random.sample(list(target_tiles), 1)

            else:
                # This is our default execution. We simply take the persona to the
                # location where the current action is taking place.
                # Retrieve the target addresses. Again, plan is an action address in its
                # string form. <maze.address_tiles> takes this and returns candidate
                # coordinates.
                address_tiles = self.rc.env.observe()["address_tiles"]
                if plan not in address_tiles:
                    address_tiles["Johnson Park:park:park garden"]  # ERRORRRRRRR
                else:
                    target_tiles = address_tiles[plan]

            # There are sometimes more than one tile returned from this (e.g., a tabe
            # may stretch many coordinates). So, we sample a few here. And from that
            # random sample, we will take the closest ones.
            if len(target_tiles) < 4:
                target_tiles = random.sample(list(target_tiles), len(target_tiles))
            else:
                target_tiles = random.sample(list(target_tiles), 4)
            # If possible, we want personas to occupy different tiles when they are
            # headed to the same location on the maze. It is ok if they end up on the
            # same time, but we try to lower that probability.
            # We take care of that overlap here.
            persona_name_set = set(roles.keys())
            new_target_tiles = []
            for i in target_tiles:
                access_tile = self.rc.env.observe(EnvObsParams(obs_type=EnvObsType.GET_TITLE, coord=i))
                curr_event_set = access_tile["events"]
                pass_curr_tile = False
                for j in curr_event_set:
                    if j[0] in persona_name_set:
                        pass_curr_tile = True
                if not pass_curr_tile:
                    new_target_tiles += [i]
            if len(new_target_tiles) == 0:
                new_target_tiles = target_tiles
            target_tiles = new_target_tiles

            # Now that we've identified the target tile, we find the shortest path to
            # one of the target tiles.
            curr_tile = self.rc.scratch.curr_tile
            closest_target_tile = None
            path = None
            for i in target_tiles:
                # path_finder takes a collision_mze and the curr_tile coordinate as
                # an input, and returns a list of coordinate tuples that becomes the
                # path.
                # e.g., [(0, 1), (1, 1), (1, 2), (1, 3), (1, 4)...]
                collision_maze = self.rc.env.observe()["collision_maze"]
                curr_path = path_finder(collision_maze, curr_tile, i, collision_block_id)
                if not closest_target_tile:
                    closest_target_tile = i
                    path = curr_path
                elif len(curr_path) < len(path):
                    closest_target_tile = i
                    path = curr_path

            # Actually setting the <planned_path> and <act_path_set>. We cut the
            # first element in the planned_path because it includes the curr_tile.
            self.rc.scratch.planned_path = path[1:]
            self.rc.scratch.act_path_set = True

        # Setting up the next immediate step. We stay at our curr_tile if there is
        # no <planned_path> left, but otherwise, we go to the next tile in the path.
        ret = self.rc.scratch.curr_tile
        if self.rc.scratch.planned_path:
            ret = self.rc.scratch.planned_path[0]
            self.rc.scratch.planned_path = self.rc.scratch.planned_path[1:]

        description = f"{self.rc.scratch.act_description}"
        description += f" @ {self.rc.scratch.act_address}"

        execution = ret, self.rc.scratch.act_pronunciatio, description
        return execution