def get_reverse_path_info(self, filtered_relation=None):
        to_opts = self.model._meta
        from_opts = self.remote_field.model._meta
        return [
            PathInfo(
                from_opts=from_opts,
                to_opts=to_opts,
                target_fields=(to_opts.pk,),
                join_field=self.remote_field,
                m2m=False,
                direct=False,
                filtered_relation=filtered_relation,
            )
        ]