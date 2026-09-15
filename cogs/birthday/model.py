class User(object):
    def __init__(
        self, discordId: int, birth_month: int, birth_day: int, birth_year: int
    ):
        self.__discordId = discordId
        self.__birth_month = birth_month
        self.__birth_day = birth_day
        self.__birth_year = birth_year

    @property
    def discordId(self):
        return self.__discordId

    @discordId.setter
    def discordId(self, discordId):
        self.__discordId = discordId

    @property
    def birth_month(self):
        return self.__birth_month

    @birth_month.setter
    def birth_month(self, birth_month):
        self.__birth_month = birth_month

    @property
    def birth_day(self):
        return self.__birth_day

    @birth_day.setter
    def birth_day(self, birth_day):
        self.__birth_day = birth_day

    @property
    def birth_year(self):
        return self.__birth_year

    @birth_year.setter
    def birth_year(self, birth_year):
        self.__birth_year = birth_year

    def __repr__(self) -> str:
        return f"User: discordId - {self.__discordId} | birthday: {self.__birth_month}/{self.__birth_day}/{self.__birth_year})"
