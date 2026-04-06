def aux(lines):
        mock = mocker.patch('io.open')
        mock.return_value.__enter__ \
            .return_value.readlines.return_value = lines