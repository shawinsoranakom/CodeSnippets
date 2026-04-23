async def async_test_func(user):
            return await user.ahas_perms(["auth_tests.add_customuser"])