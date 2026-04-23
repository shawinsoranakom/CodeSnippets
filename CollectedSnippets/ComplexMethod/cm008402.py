def extract_interaction_statistic(e):
            interaction_statistic = e.get('interactionStatistic')
            if isinstance(interaction_statistic, dict):
                interaction_statistic = [interaction_statistic]
            if not isinstance(interaction_statistic, list):
                return
            for is_e in interaction_statistic:
                if not is_type(is_e, 'InteractionCounter'):
                    continue
                interaction_type = extract_interaction_type(is_e)
                if not interaction_type:
                    continue
                # For interaction count some sites provide string instead of
                # an integer (as per spec) with non digit characters (e.g. ",")
                # so extracting count with more relaxed str_to_int
                interaction_count = str_to_int(is_e.get('userInteractionCount'))
                if interaction_count is None:
                    continue
                count_kind = INTERACTION_TYPE_MAP.get(interaction_type.split('/')[-1])
                if not count_kind:
                    continue
                count_key = f'{count_kind}_count'
                if info.get(count_key) is not None:
                    continue
                info[count_key] = interaction_count