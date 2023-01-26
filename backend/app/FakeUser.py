class FakeUser:
    def __getattr__(self, name):
        return None


fUser = FakeUser()
