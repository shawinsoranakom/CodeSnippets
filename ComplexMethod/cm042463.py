def store_iterate(self, filename: str = '', overwrite=False):
        """
        Stores the current iterate of the ocp solver in a json file.

            :param filename: if not set, use f'{self.model_name}_iterate.json'
            :param overwrite: if false and filename exists add timestamp to filename
        """
        if filename == '':
            filename = f'{self.model_name}_iterate.json'

        if not overwrite:
            # append timestamp
            if os.path.isfile(filename):
                filename = filename[:-5]
                filename += datetime.utcnow().strftime('%Y-%m-%d-%H:%M:%S.%f') + '.json'

        # get iterate:
        solution = dict()

        lN = len(str(self.N+1))
        for i in range(self.N+1):
            i_string = f'{i:0{lN}d}'
            solution['x_'+i_string] = self.get(i,'x')
            solution['u_'+i_string] = self.get(i,'u')
            solution['z_'+i_string] = self.get(i,'z')
            solution['lam_'+i_string] = self.get(i,'lam')
            solution['t_'+i_string] = self.get(i, 't')
            solution['sl_'+i_string] = self.get(i, 'sl')
            solution['su_'+i_string] = self.get(i, 'su')
            if i < self.N:
                solution['pi_'+i_string] = self.get(i,'pi')

        for k in list(solution.keys()):
            if len(solution[k]) == 0:
                del solution[k]

        # save
        with open(filename, 'w') as f:
            json.dump(solution, f, default=make_object_json_dumpable, indent=4, sort_keys=True)
        print("stored current iterate in ", os.path.join(os.getcwd(), filename))