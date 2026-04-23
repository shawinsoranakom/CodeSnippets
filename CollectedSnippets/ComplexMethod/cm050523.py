def _prepare_personal_stages_deletion(self, remaining_stages_dict, personal_stages_to_update):
        """ _prepare_personal_stages_deletion prepare the deletion of personal stages of a single user.
            Tasks using that stage will be moved to the first stage with a lower sequence if it exists
            higher if not.
        :param self: project.task.type recordset containing the personal stage of a user
                     that need to be deleted
        :param remaining_stages_dict: list of dict representation of the personal stages of a user that
                                      can be used to replace the deleted ones. Can not be empty.
                                      e.g: [{'id': stage1_id, 'seq': stage1_sequence}, ...]
        :param personal_stages_to_update: project.task.stage.personal recordset containing the records
                                          that need to be updated after stage modification. Is passed to
                                          this method as an argument to avoid to reload it for each users
                                          when this method is called multiple times.
        """
        stages_to_delete_dict = sorted([{'id': stage.id, 'seq': stage.sequence} for stage in self],
                                       key=lambda stage: stage['seq'])
        replacement_stage_id = remaining_stages_dict.pop()['id']
        next_replacement_stage = remaining_stages_dict and remaining_stages_dict.pop()

        personal_stages_by_stage = {
            stage.id: personal_stages
            for stage, personal_stages in personal_stages_to_update
        }
        for stage in stages_to_delete_dict:
            while next_replacement_stage and next_replacement_stage['seq'] < stage['seq']:
                replacement_stage_id = next_replacement_stage['id']
                next_replacement_stage = remaining_stages_dict and remaining_stages_dict.pop()
            if stage['id'] in personal_stages_by_stage:
                personal_stages_by_stage[stage['id']].stage_id = replacement_stage_id