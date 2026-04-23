def get_path_info(self, filtered_relation=None):
        if filtered_relation:
            return self.field.get_reverse_path_info(filtered_relation)
        else:
            return self.field.reverse_path_infos