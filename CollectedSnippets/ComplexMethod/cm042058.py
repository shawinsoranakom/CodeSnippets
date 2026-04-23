async def _merge_participant(self, entry: SPO, class_name: str):
        """
        Augments the sequence diagram of `class_name` to the sequence diagram of `entry`.

        Args:
            entry (SPO): The SPO object representing the base sequence diagram.
            class_name (str): The class name whose sequence diagram is to be augmented.
        """
        rows = await self.graph_db.select(predicate=GraphKeyword.IS, object_=GraphKeyword.CLASS)
        participants = []
        for r in rows:
            name = split_namespace(r.subject)[-1]
            if name == class_name:
                participants.append(r)
        if len(participants) == 0:  # external participants
            await self.graph_db.insert(
                subject=entry.subject, predicate=GraphKeyword.HAS_PARTICIPANT, object_=concat_namespace("?", class_name)
            )
            return
        if len(participants) > 1:
            for r in participants:
                await self.graph_db.insert(
                    subject=entry.subject, predicate=GraphKeyword.HAS_PARTICIPANT, object_=auto_namespace(r.subject)
                )
            return

        participant = participants[0]
        await self._rebuild_sequence_view(participant.subject)
        sequence_views = await self.graph_db.select(
            subject=participant.subject, predicate=GraphKeyword.HAS_SEQUENCE_VIEW
        )
        if not sequence_views:  # external class
            return
        rows = await self.graph_db.select(subject=entry.subject, predicate=GraphKeyword.HAS_SEQUENCE_VIEW)
        prompt = f"```mermaid\n{sequence_views[0].object_}\n```\n---\n```mermaid\n{rows[0].object_}\n```"

        rsp = await self.llm.aask(
            prompt,
            system_msgs=[
                "You are a tool to merge sequence diagrams into one.",
                "Participants with the same name are considered identical.",
                "Return the merged Mermaid sequence diagram in a markdown code block format.",
            ],
            stream=False,
        )

        sequence_view = rsp.removeprefix("```mermaid").removesuffix("```")
        rows = await self.graph_db.select(subject=entry.subject, predicate=GraphKeyword.HAS_SEQUENCE_VIEW)
        for r in rows:
            await self.graph_db.delete(subject=r.subject, predicate=r.predicate, object_=r.object_)
        await self.graph_db.insert(
            subject=entry.subject, predicate=GraphKeyword.HAS_SEQUENCE_VIEW, object_=sequence_view
        )
        await self.graph_db.insert(
            subject=entry.subject,
            predicate=GraphKeyword.HAS_SEQUENCE_VIEW_VER,
            object_=concat_namespace(datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3], add_affix(sequence_view)),
        )
        await self.graph_db.insert(
            subject=entry.subject, predicate=GraphKeyword.HAS_PARTICIPANT, object_=auto_namespace(participant.subject)
        )
        await self._save_sequence_view(subject=entry.subject, content=sequence_view)