def test_exclude_many_to_many(self):
        i_extra = Identifier.objects.create(name="extra")
        i_program = Identifier.objects.create(name="program")
        program = Program.objects.create(identifier=i_program)
        i_channel = Identifier.objects.create(name="channel")
        channel = Channel.objects.create(identifier=i_channel)
        channel.programs.add(program)

        # channel contains 'program1', so all Identifiers except that one
        # should be returned
        self.assertSequenceEqual(
            Identifier.objects.exclude(program__channel=channel).order_by("name"),
            [i_channel, i_extra],
        )
        self.assertSequenceEqual(
            Identifier.objects.exclude(program__channel=None).order_by("name"),
            [i_program],
        )