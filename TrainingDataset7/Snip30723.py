def setUpTestData(cls):
        cls.school = School.objects.create()
        cls.room_1 = Classroom.objects.create(
            school=cls.school, has_blackboard=False, name="Room 1"
        )
        cls.room_2 = Classroom.objects.create(
            school=cls.school, has_blackboard=True, name="Room 2"
        )
        cls.room_3 = Classroom.objects.create(
            school=cls.school, has_blackboard=True, name="Room 3"
        )
        cls.room_4 = Classroom.objects.create(
            school=cls.school, has_blackboard=False, name="Room 4"
        )
        tag = Tag.objects.create()
        cls.annotation_1 = Annotation.objects.create(tag=tag)
        annotation_2 = Annotation.objects.create(tag=tag)
        note = cls.annotation_1.notes.create(tag=tag)
        cls.base_user_1 = BaseUser.objects.create(annotation=cls.annotation_1)
        cls.base_user_2 = BaseUser.objects.create(annotation=annotation_2)
        cls.task = Task.objects.create(
            owner=cls.base_user_2,
            creator=cls.base_user_2,
            note=note,
        )