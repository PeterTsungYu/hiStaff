from pandas.tseries.holiday import AbstractHolidayCalendar, Holiday
from pandas.tseries.offsets import Day, CustomBusinessDay
import pandas as pd
from datetime import date
from pandas.tseries.offsets import CDay

class hiCalendar(AbstractHolidayCalendar):
    rules = [
        Holiday('New Years Day', month=1, day=1),
        Holiday('Labour Day', month=5, day=1)
    ]

    def __init__(self, year, month, day, month_range):
        self.year=year
        self.start=date(self.year, month, day)
        self.end=self.start + pd.offsets.MonthEnd(month_range)
        self.bdate_index = pd.bdate_range(start=self.start,
                                            end=self.end,
                                            freq=CDay(calendar=self))
        self.date_index = pd.date_range(start=self.start,
                                end=self.end,
                                freq='D')

    def holidays_index(self):
        index = self.holidays(start=self.start, end=self.end)
        return index
    def bdays_count(self):
        series = pd.bdate_range(start=self.start,
                                end=self.end,
                                freq=CDay(calendar=self)).to_series()
        return series.groupby(series.dt.month).count().head()
    def bdays_bool_df(self):
        return pd.DataFrame(data=[True if i in self.bdate_index else False for i in self.date_index] ,index=self.date_index, columns=['Woring Day'])

# Creating a series of dates between the boundaries 
# by using the custom calendar
# Counting the number of working days by month

#print(pd.DataFrame(se))
#print(se.groupby(se.dt.month).count().head())

if __name__ == "__main__":
    cal = hiCalendar(2022,1,1,12)
    print(cal.bdays_bool_df().columns)
    #print(cal.date_index())
    #print(cal.holidays_index())
    #print(cal.bdays_count())
    
    # SQLAlchemy ORM conversion to pandas DataFrame