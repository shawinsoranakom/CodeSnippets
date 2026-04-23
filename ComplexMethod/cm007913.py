def test_prepare_outtmpl_and_filename(self):
        def test(tmpl, expected, *, info=None, **params):
            params['outtmpl'] = tmpl
            ydl = FakeYDL(params)
            ydl._num_downloads = 1
            self.assertEqual(ydl.validate_outtmpl(tmpl), None)

            out = ydl.evaluate_outtmpl(tmpl, info or self.outtmpl_info)
            fname = ydl.prepare_filename(info or self.outtmpl_info)

            if not isinstance(expected, (list, tuple)):
                expected = (expected, expected)
            for (name, got), expect in zip((('outtmpl', out), ('filename', fname)), expected, strict=True):
                if callable(expect):
                    self.assertTrue(expect(got), f'Wrong {name} from {tmpl}')
                elif expect is not None:
                    self.assertEqual(got, expect, f'Wrong {name} from {tmpl}')

        # Side-effects
        original_infodict = dict(self.outtmpl_info)
        test('foo.bar', 'foo.bar')
        original_infodict['epoch'] = self.outtmpl_info.get('epoch')
        self.assertTrue(isinstance(original_infodict['epoch'], int))
        test('%(epoch)d', int_or_none)
        self.assertEqual(original_infodict, self.outtmpl_info)

        # Auto-generated fields
        test('%(id)s.%(ext)s', '1234.mp4')
        test('%(duration_string)s', ('27:46:40', '27-46-40'))
        test('%(resolution)s', '1080p')
        test('%(playlist_index|)s', '001')
        test('%(playlist_index&{}!)s', '1!')
        test('%(playlist_autonumber)s', '02')
        test('%(autonumber)s', '00001')
        test('%(autonumber+2)03d', '005', autonumber_start=3)
        test('%(autonumber)s', '001', autonumber_size=3)

        # Escaping %
        test('%', '%')
        test('%%', '%')
        test('%%%%', '%%')
        test('%s', '%s')
        test('%%%s', '%%s')
        test('%d', '%d')
        test('%abc%', '%abc%')
        test('%%(width)06d.%(ext)s', '%(width)06d.mp4')
        test('%%%(height)s', '%1080')
        test('%(width)06d.%(ext)s', 'NA.mp4')
        test('%(width)06d.%%(ext)s', 'NA.%(ext)s')
        test('%%(width)06d.%(ext)s', '%(width)06d.mp4')

        # Sanitization options
        test('%(title3)s', (None, 'foo⧸bar⧹test'))
        test('%(title5)s', (None, 'aei_A'), restrictfilenames=True)
        test('%(title3)s', (None, 'foo_bar_test'), windowsfilenames=False, restrictfilenames=True)
        if sys.platform != 'win32':
            test('%(title3)s', (None, 'foo⧸bar\\test'), windowsfilenames=False)

        # ID sanitization
        test('%(id)s', '_abcd', info={'id': '_abcd'})
        test('%(some_id)s', '_abcd', info={'some_id': '_abcd'})
        test('%(formats.0.id)s', '_abcd', info={'formats': [{'id': '_abcd'}]})
        test('%(id)s', '-abcd', info={'id': '-abcd'})
        test('%(id)s', '.abcd', info={'id': '.abcd'})
        test('%(id)s', 'ab__cd', info={'id': 'ab__cd'})
        test('%(id)s', ('ab:cd', 'ab：cd'), info={'id': 'ab:cd'})
        test('%(id.0)s', '-', info={'id': '--'})

        # Invalid templates
        self.assertTrue(isinstance(YoutubeDL.validate_outtmpl('%(title)'), ValueError))
        test('%(invalid@tmpl|def)s', 'none', outtmpl_na_placeholder='none')
        test('%(..)s', 'NA')
        test('%(formats.{id)s', 'NA')

        # Entire info_dict
        def expect_same_infodict(out):
            got_dict = json.loads(out)
            for info_field, expected in self.outtmpl_info.items():
                self.assertEqual(got_dict.get(info_field), expected, info_field)
            return True

        test('%()j', (expect_same_infodict, None))

        # NA placeholder
        NA_TEST_OUTTMPL = '%(uploader_date)s-%(width)d-%(x|def)s-%(id)s.%(ext)s'
        test(NA_TEST_OUTTMPL, 'NA-NA-def-1234.mp4')
        test(NA_TEST_OUTTMPL, 'none-none-def-1234.mp4', outtmpl_na_placeholder='none')
        test(NA_TEST_OUTTMPL, '--def-1234.mp4', outtmpl_na_placeholder='')
        test('%(non_existent.0)s', 'NA')

        # String formatting
        FMT_TEST_OUTTMPL = '%%(height)%s.%%(ext)s'
        test(FMT_TEST_OUTTMPL % 's', '1080.mp4')
        test(FMT_TEST_OUTTMPL % 'd', '1080.mp4')
        test(FMT_TEST_OUTTMPL % '6d', '  1080.mp4')
        test(FMT_TEST_OUTTMPL % '-6d', '1080  .mp4')
        test(FMT_TEST_OUTTMPL % '06d', '001080.mp4')
        test(FMT_TEST_OUTTMPL % ' 06d', ' 01080.mp4')
        test(FMT_TEST_OUTTMPL % '   06d', ' 01080.mp4')
        test(FMT_TEST_OUTTMPL % '0 6d', ' 01080.mp4')
        test(FMT_TEST_OUTTMPL % '0   6d', ' 01080.mp4')
        test(FMT_TEST_OUTTMPL % '   0   6d', ' 01080.mp4')

        # Type casting
        test('%(id)d', '1234')
        test('%(height)c', '1')
        test('%(ext)c', 'm')
        test('%(id)d %(id)r', "1234 '1234'")
        test('%(id)r %(height)r', "'1234' 1080")
        test('%(title5)a %(height)a', (R"'\xe1\xe9\xed \U0001d400' 1080", None))
        test('%(ext)s-%(ext|def)d', 'mp4-def')
        test('%(width|0)04d', '0')
        test('a%(width|b)d', 'ab', outtmpl_na_placeholder='none')

        FORMATS = self.outtmpl_info['formats']

        # Custom type casting
        test('%(formats.:.id)l', 'id 1, id 2, id 3')
        test('%(formats.:.id)#l', ('id 1\nid 2\nid 3', 'id 1 id 2 id 3'))
        test('%(ext)l', 'mp4')
        test('%(formats.:.id) 18l', '  id 1, id 2, id 3')
        test('%(formats)j', (json.dumps(FORMATS), None))
        test('%(formats)#j', (
            json.dumps(FORMATS, indent=4),
            json.dumps(FORMATS, indent=4).replace(':', '：').replace('"', '＂').replace('\n', ' '),
        ))
        test('%(title5).3B', 'á')
        test('%(title5)U', 'áéí 𝐀')
        test('%(title5)#U', 'a\u0301e\u0301i\u0301 𝐀')
        test('%(title5)+U', 'áéí A')
        test('%(title5)+#U', 'a\u0301e\u0301i\u0301 A')
        test('%(height)D', '1k')
        test('%(filesize)#D', '1Ki')
        test('%(height)5.2D', ' 1.08k')
        test('%(title4)#S', 'foo_bar_test')
        test('%(title4).10S', ('foo ＂bar＂ ', 'foo ＂bar＂' + ('#' if os.name == 'nt' else ' ')))
        if os.name == 'nt':
            test('%(title4)q', ('"foo ""bar"" test"', None))
            test('%(formats.:.id)#q', ('"id 1" "id 2" "id 3"', None))
            test('%(formats.0.id)#q', ('"id 1"', None))
        else:
            test('%(title4)q', ('\'foo "bar" test\'', '\'foo ＂bar＂ test\''))
            test('%(formats.:.id)#q', "'id 1' 'id 2' 'id 3'")
            test('%(formats.0.id)#q', "'id 1'")

        # Internal formatting
        test('%(timestamp-1000>%H-%M-%S)s', '11-43-20')
        test('%(title|%)s %(title|%%)s', '% %%')
        test('%(id+1-height+3)05d', '00158')
        test('%(width+100)05d', 'NA')
        test('%(filesize*8)d', '8192')
        test('%(formats.0) 15s', ('% 15s' % FORMATS[0], None))
        test('%(formats.0)r', (repr(FORMATS[0]), None))
        test('%(height.0)03d', '001')
        test('%(-height.0)04d', '-001')
        test('%(formats.-1.id)s', FORMATS[-1]['id'])
        test('%(formats.0.id.-1)d', FORMATS[0]['id'][-1])
        test('%(formats.3)s', 'NA')
        test('%(formats.:2:-1)r', repr(FORMATS[:2:-1]))
        test('%(formats.0.id.-1+id)f', '1235.000000')
        test('%(formats.0.id.-1+formats.1.id.-1)d', '3')
        out = json.dumps([{'id': f['id'], 'height.:2': str(f['height'])[:2]}
                          if 'height' in f else {'id': f['id']}
                          for f in FORMATS])
        test('%(formats.:.{id,height.:2})j', (out, None))
        test('%(formats.:.{id,height}.id)l', ', '.join(f['id'] for f in FORMATS))
        test('%(.{id,title})j', ('{"id": "1234"}', '{＂id＂： ＂1234＂}'))

        # Alternates
        test('%(title,id)s', '1234')
        test('%(width-100,height+20|def)d', '1100')
        test('%(width-100,height+width|def)s', 'def')
        test('%(timestamp-x>%H\\,%M\\,%S,timestamp>%H\\,%M\\,%S)s', '12,00,00')

        # Replacement
        test('%(id&foo)s.bar', 'foo.bar')
        test('%(title&foo)s.bar', 'NA.bar')
        test('%(title&foo|baz)s.bar', 'baz.bar')
        test('%(x,id&foo|baz)s.bar', 'foo.bar')
        test('%(x,title&foo|baz)s.bar', 'baz.bar')
        test('%(id&a\nb|)s', ('a\nb', 'a b'))
        test('%(id&hi {:>10} {}|)s', 'hi       1234 1234')
        test(R'%(id&{0} {}|)s', 'NA')
        test(R'%(id&{0.1}|)s', 'NA')
        test('%(height&{:,d})S', '1,080')

        # Laziness
        def gen():
            yield from range(5)
            raise self.assertTrue(False, 'LazyList should not be evaluated till here')
        test('%(key.4)s', '4', info={'key': LazyList(gen())})

        # Empty filename
        test('%(foo|)s-%(bar|)s.%(ext)s', '-.mp4')
        # test('%(foo|)s.%(ext)s', ('.mp4', '_.mp4'))  # FIXME: ?
        # test('%(foo|)s', ('', '_'))  # FIXME: ?

        # Environment variable expansion for prepare_filename
        os.environ['__yt_dlp_var'] = 'expanded'
        envvar = '%__yt_dlp_var%' if os.name == 'nt' else '$__yt_dlp_var'
        test(envvar, (envvar, 'expanded'))
        if os.name == 'nt':
            test('%s%', ('%s%', '%s%'))
            os.environ['s'] = 'expanded'
            test('%s%', ('%s%', 'expanded'))  # %s% should be expanded before escaping %s
            os.environ['(test)s'] = 'expanded'
            test('%(test)s%', ('NA%', 'expanded'))  # Environment should take priority over template

        # Path expansion and escaping
        test('Hello %(title1)s', 'Hello $PATH')
        test('Hello %(title2)s', 'Hello %PATH%')
        test('%(title3)s', ('foo/bar\\test', 'foo⧸bar⧹test'))
        test('folder/%(title3)s', ('folder/foo/bar\\test', f'folder{os.path.sep}foo⧸bar⧹test'))