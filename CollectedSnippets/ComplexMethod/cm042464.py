def dump_last_qp_to_json(self, filename: str = '', overwrite=False):
        """
        Dumps the latest QP data into a json file

            :param filename: if not set, use model_name + timestamp + '.json'
            :param overwrite: if false and filename exists add timestamp to filename
        """
        if filename == '':
            filename = f'{self.model_name}_QP.json'

        if not overwrite:
            # append timestamp
            if os.path.isfile(filename):
                filename = filename[:-5]
                filename += datetime.utcnow().strftime('%Y-%m-%d-%H:%M:%S.%f') + '.json'

        # get QP data:
        qp_data = dict()

        lN = len(str(self.N+1))
        for field in self.__qp_dynamics_fields:
            for i in range(self.N):
                qp_data[f'{field}_{i:0{lN}d}'] = self.get_from_qp_in(i,field)

        for field in self.__qp_constraint_fields + self.__qp_cost_fields:
            for i in range(self.N+1):
                qp_data[f'{field}_{i:0{lN}d}'] = self.get_from_qp_in(i,field)

        # remove empty fields
        for k in list(qp_data.keys()):
            if len(qp_data[k]) == 0:
                del qp_data[k]

        # save
        with open(filename, 'w') as f:
            json.dump(qp_data, f, default=make_object_json_dumpable, indent=4, sort_keys=True)
        print("stored qp from solver memory in ", os.path.join(os.getcwd(), filename))