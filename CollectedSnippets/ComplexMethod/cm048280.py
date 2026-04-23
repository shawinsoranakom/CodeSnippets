def _match(rules):
            for rule in rules:
                # url might not be set because it comes from referer, in that
                # case match the first rule with no regex_url
                if not re.search(rule.regex_url or "", url or ""):
                    continue
                if rule.chatbot_script_id and (
                    not rule.chatbot_script_id.active or not rule.chatbot_script_id.script_step_ids
                ):
                    continue
                if (
                    rule.chatbot_enabled_condition == "only_if_operator"
                    and not rule.channel_id.available_operator_ids
                    or rule.chatbot_enabled_condition == "only_if_no_operator"
                    and rule.channel_id.available_operator_ids
                ):
                    continue
                return rule
            return self.env["im_livechat.channel.rule"]