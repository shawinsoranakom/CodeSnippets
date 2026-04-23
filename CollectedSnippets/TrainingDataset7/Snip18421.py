def get_user_data(self, user):
        return {
            "username": user.username,
            "password": user.password,
            "email": user.email,
            "is_active": user.is_active,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "last_login_0": user.last_login.strftime("%Y-%m-%d"),
            "last_login_1": user.last_login.strftime("%H:%M:%S"),
            "initial-last_login_0": user.last_login.strftime("%Y-%m-%d"),
            "initial-last_login_1": user.last_login.strftime("%H:%M:%S"),
            "date_joined_0": user.date_joined.strftime("%Y-%m-%d"),
            "date_joined_1": user.date_joined.strftime("%H:%M:%S"),
            "initial-date_joined_0": user.date_joined.strftime("%Y-%m-%d"),
            "initial-date_joined_1": user.date_joined.strftime("%H:%M:%S"),
            "first_name": user.first_name,
            "last_name": user.last_name,
        }