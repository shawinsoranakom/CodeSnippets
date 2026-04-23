def test_filewriter_metadata_writing(self, filename):
        sd = torch.nn.Linear(3, 5).state_dict()
        weight_nbytes = sd['weight'].untyped_storage().nbytes()
        bias_nbytes = sd['bias'].untyped_storage().nbytes()
        # TemporaryFileName will give a string
        # NamedTemporaryFile will be treated as a buffer
        file_creation_func = TemporaryFileName if filename else functools.partial(tempfile.NamedTemporaryFile, delete=False)

        with file_creation_func() as f, file_creation_func() as g:
            # save state_dict in f
            torch.save(sd, f)
            if not filename:
                f.seek(0)
            # extract 'data.pkl' for use in our fake checkpoint
            with torch.serialization._open_file_like(f, 'rb') as opened_file:
                with torch.serialization._open_zipfile_reader(opened_file) as zip_file:
                    data_file = io.BytesIO(zip_file.get_record('data.pkl'))
                    data_0_offset = zip_file.get_record_offset('data/0')
                    data_1_offset = zip_file.get_record_offset('data/1')
            if not filename:
                f.close()

            # write nulls for 'data/0' and 'data/1'
            with open(f if filename else f.name, 'rb+') as opened_f:
                opened_f.seek(data_0_offset)
                opened_f.write(b'0' * weight_nbytes)
                opened_f.seek(data_1_offset)
                opened_f.write(b'0' * bias_nbytes)

            with torch.serialization._open_zipfile_writer(g) as zip_file:
                data_value = data_file.getvalue()
                zip_file.write_record('data.pkl', data_value, len(data_value))
                zip_file.write_record('byteorder', sys.byteorder, len(sys.byteorder))
                # Only write metadata for storages
                zip_file.write_record_metadata('data/0', weight_nbytes)
                zip_file.write_record_metadata('data/1', bias_nbytes)

            if not filename:
                g.seek(0)
            sd_loaded = torch.load(g)
            with open(f if filename else f.name, 'rb') as opened_f:
                sd_loaded_ref = torch.load(opened_f)
                self.assertEqual(sd_loaded, sd_loaded_ref)
            if not filename:
                os.unlink(f.name)
                g.close()
                os.unlink(g.name)