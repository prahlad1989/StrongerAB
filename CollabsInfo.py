class CollabsInfo:
    def __init__(self, *args, **kwargs):
        self.__total =0
        self__total_minus_ok=0
        self.paid = 0
        self.unpaid = 0
        self.ok = 0
        self.country = None
        self.manager = None

    paid = 0
    unpaid =0
    ok =0

    @property
    def total(self):
        return self.paid+ self.unpaid+self.ok

    @property
    def total_minus_ok(self):
        return self.paid+ self.unpaid

    def toProperDict(self):
        newDict = {}
        for key,value in self.__dict__.items():
            newDict[key.replace("_CollabsInfo__","")] = value
        newDict['total'] = self.total
        newDict['totoal_minus_ok'] = self.total_minus_ok
        return newDict





