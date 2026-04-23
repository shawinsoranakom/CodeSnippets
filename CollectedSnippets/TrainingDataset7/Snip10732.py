def get_del_batches(self, objs, fields):
        """
        Return the objs in suitably sized batches for the used connection.
        """
        conn_batch_size = max(
            connections[self.using].ops.bulk_batch_size(fields, objs), 1
        )
        if len(objs) > conn_batch_size:
            return [
                objs[i : i + conn_batch_size]
                for i in range(0, len(objs), conn_batch_size)
            ]
        else:
            return [objs]