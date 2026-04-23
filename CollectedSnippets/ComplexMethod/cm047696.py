def add_default(self,**params):
        if len(self.profiles_raw) > 1:
            if params['combined_profile']:
                self.add_output(self.profiles_raw, display_name='Combined', **params)
        for key, profile in self.profiles_raw.items():
            sql = profile and profile[0].get('query')
            if sql:
                if params['sql_no_gap_profile']:
                    self.add_output([key], hide_gaps=True, display_name=f'{key} (no gap)', **params)
                if params['sql_density_profile']:
                    self.add_output([key], continuous=False, complete=False, display_name=f'{key} (density)',**params)

            elif params['frames_profile']:
                    self.add_output([key], display_name=key,**params)
        return self