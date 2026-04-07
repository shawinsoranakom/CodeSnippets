def authenticate(
                self,
                request: HttpRequest,
                username: AnnotatedUsername,
                password: AnnotatedPassword,
            ) -> User | None:
                return self.invariant_user