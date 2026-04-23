def formatted_read_group(self, domain, groupby=(), aggregates=(), having=(), offset=0, limit=None, order=None):
        # Update chatbot_answers_path label: ids are used for grouping but names
        # should be displayed.
        result = super().formatted_read_group(
            domain, groupby, aggregates, having=having, offset=offset, limit=limit, order=order
        )
        answer_ids = {
            int(answer_id.strip())
            for entry in result
            if entry.get("chatbot_answers_path")
            for answer_id in entry["chatbot_answers_path"].split("-")
        }
        answer_name_by_id = {
            answer.id: answer.name
            for answer in self.env["chatbot.script.answer"].search_fetch(
                [("id", "in", answer_ids)],
                ["name"],
            )
        }
        for entry in result:
            if not (path := entry.get("chatbot_answers_path")):
                continue
            id_list = [int(answer_id.strip()) for answer_id in path.split("-")]
            entry["chatbot_answers_path"] = " - ".join(
                answer_name_by_id.get(answer_id, self._unknown_chatbot_answer_name)
                for answer_id in id_list
            )
        return result