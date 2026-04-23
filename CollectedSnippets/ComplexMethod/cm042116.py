async def test_init():
    class Inputs(BaseModel):
        name: str
        profile: str
        goal: str
        constraints: str
        desc: str
        kwargs: Optional[Dict] = None
        expect_name: str
        expect_profile: str
        expect_goal: str
        expect_constraints: str
        expect_desc: str
        exclude: list = Field(default_factory=list)

    inputs = [
        {
            "name": "Lily{language}",
            "expect_name": "Lily{language}",
            "profile": "X {teaching_language}",
            "expect_profile": "X {teaching_language}",
            "goal": "Do {something_big}, {language}",
            "expect_goal": "Do {something_big}, {language}",
            "constraints": "Do in {key1}, {language}",
            "expect_constraints": "Do in {key1}, {language}",
            "kwargs": {},
            "desc": "aaa{language}",
            "expect_desc": "aaa{language}",
            "exclude": ["language", "key1", "something_big", "teaching_language"],
        },
        {
            "name": "Lily{language}",
            "expect_name": "LilyCN",
            "profile": "X {teaching_language}",
            "expect_profile": "X EN",
            "goal": "Do {something_big}, {language}",
            "expect_goal": "Do sleep, CN",
            "constraints": "Do in {key1}, {language}",
            "expect_constraints": "Do in HaHa, CN",
            "kwargs": {"language": "CN", "key1": "HaHa", "something_big": "sleep", "teaching_language": "EN"},
            "desc": "aaa{language}",
            "expect_desc": "aaaCN",
            "language": "CN",
            "teaching_language": "EN",
        },
    ]

    for i in inputs:
        seed = Inputs(**i)
        context = Context()
        for k in seed.exclude:
            context.kwargs.set(k, None)
        for k, v in seed.kwargs.items():
            context.kwargs.set(k, v)

        teacher = Teacher(
            context=context,
            name=seed.name,
            profile=seed.profile,
            goal=seed.goal,
            constraints=seed.constraints,
            desc=seed.desc,
        )
        assert teacher.name == seed.expect_name
        assert teacher.desc == seed.expect_desc
        assert teacher.profile == seed.expect_profile
        assert teacher.goal == seed.expect_goal
        assert teacher.constraints == seed.expect_constraints
        assert teacher.course_title == "teaching_plan"