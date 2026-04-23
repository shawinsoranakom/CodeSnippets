async def observe(self) -> list[BasicMemory]:
        # TODO observe info from maze_env
        """
        Perceive events around the role and saves it to the memory, both events
        and spaces.

        We first perceive the events nearby the role, as determined by its
        <vision_r>. If there are a lot of events happening within that radius, we
        take the <att_bandwidth> of the closest events. Finally, we check whether
        any of them are new, as determined by <retention>. If they are new, then we
        save those and return the <BasicMemory> instances for those events.

        OUTPUT:
            ret_events: a list of <BasicMemory> that are perceived and new.
        """
        # PERCEIVE SPACE
        # We get the nearby tiles given our current tile and the persona's vision
        # radius.
        nearby_tiles = self.rc.env.observe(
            EnvObsParams(
                obs_type=EnvObsType.TILE_NBR, coord=self.rc.scratch.curr_tile, vision_radius=self.rc.scratch.vision_r
            )
        )

        # We then store the perceived space. Note that the s_mem of the persona is
        # in the form of a tree constructed using dictionaries.
        for tile in nearby_tiles:
            tile_info = self.rc.env.observe(EnvObsParams(obs_type=EnvObsType.GET_TITLE, coord=tile))
            self.rc.spatial_memory.add_tile_info(tile_info)

        # PERCEIVE EVENTS.
        # We will perceive events that take place in the same arena as the
        # persona's current arena.

        curr_arena_path = self.rc.env.observe(
            EnvObsParams(obs_type=EnvObsType.TILE_PATH, coord=self.rc.scratch.curr_tile, level="arena")
        )

        # We do not perceive the same event twice (this can happen if an object is
        # extended across multiple tiles).
        percept_events_set = set()
        # We will order our percept based on the distance, with the closest ones
        # getting priorities.
        percept_events_list = []
        # First, we put all events that are occurring in the nearby tiles into the
        # percept_events_list
        for tile in nearby_tiles:
            tile_details = self.rc.env.observe(EnvObsParams(obs_type=EnvObsType.GET_TITLE, coord=tile))
            if tile_details["events"]:
                tmp_arena_path = self.rc.env.observe(
                    EnvObsParams(obs_type=EnvObsType.TILE_PATH, coord=tile, level="arena")
                )

                if tmp_arena_path == curr_arena_path:
                    # This calculates the distance between the persona's current tile,
                    # and the target tile.
                    dist = math.dist([tile[0], tile[1]], [self.rc.scratch.curr_tile[0], self.rc.scratch.curr_tile[1]])
                    # Add any relevant events to our temp set/list with the distant info.
                    for event in tile_details["events"]:
                        if event not in percept_events_set:
                            percept_events_list += [[dist, event]]
                            percept_events_set.add(event)

        # We sort, and perceive only self.rc.scratch.att_bandwidth of the closest
        # events. If the bandwidth is larger, then it means the persona can perceive
        # more elements within a small area.
        percept_events_list = sorted(percept_events_list, key=itemgetter(0))
        perceived_events = []
        for dist, event in percept_events_list[: self.rc.scratch.att_bandwidth]:
            perceived_events += [event]

        # Storing events.
        # <ret_events> is a list of <BasicMemory> instances from the persona's
        # associative memory.
        ret_events = []
        for p_event in perceived_events:
            s, p, o, desc = p_event
            if not p:
                # If the object is not present, then we default the event to "idle".
                p = "is"
                o = "idle"
                desc = "idle"
            desc = f"{s.split(':')[-1]} is {desc}"
            p_event = (s, p, o)

            # We retrieve the latest self.rc.scratch.retention events. If there is
            # something new that is happening (that is, p_event not in latest_events),
            # then we add that event to the a_mem and return it.
            latest_events = self.rc.memory.get_summarized_latest_events(self.rc.scratch.retention)
            if p_event not in latest_events:
                # We start by managing keywords.
                keywords = set()
                sub = p_event[0]
                obj = p_event[2]
                if ":" in p_event[0]:
                    sub = p_event[0].split(":")[-1]
                if ":" in p_event[2]:
                    obj = p_event[2].split(":")[-1]
                keywords.update([sub, obj])

                # Get event embedding
                desc_embedding_in = desc
                if "(" in desc:
                    desc_embedding_in = desc_embedding_in.split("(")[1].split(")")[0].strip()
                if desc_embedding_in in self.rc.memory.embeddings:
                    event_embedding = self.rc.memory.embeddings[desc_embedding_in]
                else:
                    event_embedding = get_embedding(desc_embedding_in)
                event_embedding_pair = (desc_embedding_in, event_embedding)

                # Get event poignancy.
                event_poignancy = await generate_poig_score(self, "event", desc_embedding_in)
                logger.debug(f"Role {self.name} event_poignancy: {event_poignancy}")

                # If we observe the persona's self chat, we include that in the memory
                # of the persona here.
                chat_node_ids = []
                if p_event[0] == f"{self.name}" and p_event[1] == "chat with":
                    curr_event = self.rc.scratch.act_event
                    if self.rc.scratch.act_description in self.rc.memory.embeddings:
                        chat_embedding = self.rc.memory.embeddings[self.rc.scratch.act_description]
                    else:
                        chat_embedding = get_embedding(self.rc.scratch.act_description)
                    chat_embedding_pair = (self.rc.scratch.act_description, chat_embedding)
                    chat_poignancy = await generate_poig_score(self, "chat", self.rc.scratch.act_description)
                    chat_node = self.rc.memory.add_chat(
                        self.rc.scratch.curr_time,
                        None,
                        curr_event[0],
                        curr_event[1],
                        curr_event[2],
                        self.rc.scratch.act_description,
                        keywords,
                        chat_poignancy,
                        chat_embedding_pair,
                        self.rc.scratch.chat,
                    )
                    chat_node_ids = [chat_node.memory_id]

                # Finally, we add the current event to the agent's memory.
                ret_events += [
                    self.rc.memory.add_event(
                        self.rc.scratch.curr_time,
                        None,
                        s,
                        p,
                        o,
                        desc,
                        keywords,
                        event_poignancy,
                        event_embedding_pair,
                        chat_node_ids,
                    )
                ]
                self.rc.scratch.importance_trigger_curr -= event_poignancy
                self.rc.scratch.importance_ele_n += 1

        return ret_events