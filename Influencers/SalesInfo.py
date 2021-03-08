class SalesInfo:
    def __init__(self, *args, **kwargs):
        self.__country = None
        self.__country_sales = 0
        self.__voucher_sales = 0
        self.__product_cost = 0
        self.__commission = 0
        self.__total_cost = 0
        self.__roas = 0
        self.__percent_total_sales = 0
        self.__influe_to_country_sales_ratio = 0

    country = None
    country_sales = 0
    voucher_sales = 0
    product_cost = 0
    commission = 0
    total_cost = 0
    roas =0
    percent_total_sales =0
    influe_to_country_sales_ratio=0


    @property
    def percent_total_sales(self):
        return  self.__percent_total_sales

    @percent_total_sales.setter
    def percent_total_sales(self, percent_total_sales):
        self.__percent_total_sales = percent_total_sales

    @property
    def influe_to_country_sales_ratio(self):
        return self.__influe_to_country_sales_ratio

    @influe_to_country_sales_ratio.setter
    def influe_to_country_sales_ratio(self, influe_to_country_sales_ratio):
        self.__influe_to_country_sales_ratio = influe_to_country_sales_ratio

    @property
    def country(self):
        return self.__country

    @country.setter
    def country(self, country):
        if country:
            self.__country = country

    @property
    def country_sales(self):
        return self.__country_sales

    @country_sales.setter
    def country_sales(self, country_sales):
        if country_sales is None:
            self.__country_sales = 0
        else:
            self.__country_sales = country_sales

    @property
    def voucher_sales(self):
        return self.__voucher_sales

    @voucher_sales.setter
    def voucher_sales(self, voucher_sales):
        if voucher_sales is None:
            self.__voucher_sales = 0
        else:
            self.__voucher_sales = voucher_sales

    @property
    def product_cost(self):
        return self.__product_cost

    @product_cost.setter
    def product_cost(self, product_cost):
        self.__product_cost = 0 if product_cost is None else product_cost

    @property
    def commission(self):
        return self.__commission

    @commission.setter
    def commission(self, commission):
        self.__commission = 0 if commission is None else commission

    @property
    def total_cost(self):
        return self.__product_cost + self.__commission

    @property
    def roas(self):
        if self.total_cost:
            temp = self.voucher_sales/self.total_cost
            return temp
        return 0;


    def toProperDict(self):
        newDict = {}
        for key,value in self.__dict__.items():
            newDict[key.replace("_SalesInfo__","")] = value
        newDict['roas'] = self.roas
        newDict['total_cost'] = self.total_cost
        return newDict















