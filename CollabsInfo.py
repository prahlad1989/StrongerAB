class CollabsInfo:
    def __init__(self, *args, **kwargs):
        self.__total =0
        self.paid = 0
        self.unpaid = 0
        self.ok = 0
        self.country = None

    paid = 0
    unpaid =0
    ok =0

    @property
    def total(self):
        return self.paid+ self.unpaid+self.ok

    def toProperDict(self):
        newDict = {}
        for key,value in self.__dict__.items():
            newDict[key.replace("_CollabsInfo__","")] = value
        newDict['total'] = self.total
        return newDict





