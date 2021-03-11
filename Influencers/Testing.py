from Influencers.SalesInfo import SalesInfo
import pytz
sql_datetime_format = "%Y-%m-%d %H:%M:%S"

from datetime import datetime,timezone

s=object.__new__(SalesInfo)


s.last_name='keka'
print(s)
s2 = type(s)()
print(s2)
print(s2.first_name)
print(type(s2))
print(type(s))
x =1000000
y = x/1e6
print("y",y)
y = datetime.now()
print(y)
#z = y.astimezone(tz=timezone.utc)
z = y.astimezone(tz= pytz.timezone('Asia/Kolkata'))
print(z)
print(pytz.common_timezones)
print(pytz.all_timezones_set)

tz = pytz.timezone('Asia/Kolkata')
mytime = datetime.now(tz=tz)
print(mytime)
print(z)