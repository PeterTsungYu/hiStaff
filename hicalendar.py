from pandas.tseries.holiday import AbstractHolidayCalendar, Holiday
from pandas.tseries.offsets import Day, CustomBusinessDay
import pandas as pd
from datetime import date, datetime
from pandas.tseries.offsets import CDay # custom business day

class hiCalendar(AbstractHolidayCalendar):
    rules = [
        Holiday('New Years Day', month=1, day=1),
        Holiday('test Day', month=1, day=3),
        Holiday('Labour Day', month=5, day=1)
    ]

    def __init__(self, start, end):
        self.start=start
        self.end=end
        self.date_index = pd.date_range( # all dates
            start=self.start,  
            end=self.end,
            freq='D'
            )
    
    def bdate(self):
        # custom business days
        return pd.bdate_range( 
            start=self.start, 
            end=self.end,
            freq=CDay(calendar=self)
            )   
    def hdate(self):
        # holidays date and name
        return self.holidays(
            start=self.start,  
            end=self.end, 
            return_name=True
            )
    def bdays_count(self):
        series = self.bdate().to_series()
        return series.groupby(series.dt.month).count().head()

    def bdays_hdays(self):
        bdate_index = self.bdate()
        hdate_index = self.hdate()
        weekday_name = lambda date: hdate_index[date] if date in hdate_index.index else ('weekend' if date.weekday()+1 in [6,7] else f'weekday_{date.weekday()+1}')
        return pd.DataFrame(data=[(weekday_name(i), True) if i in bdate_index else (weekday_name(i), False) for i in self.date_index] ,index=self.date_index, columns=['weekday', 'Working Day'])
        
        

# Creating a series of dates between the boundaries 
# by using the custom calendar
# Counting the number of working days by month

#print(pd.DataFrame(se))
#print(se.groupby(se.dt.month).count().head())

if __name__ == "__main__":
    cal = hiCalendar(date(2022, 1, 1), date(2022, 7, 30))
    print(cal.bdays_hdays().loc[f'{datetime.now().date()}', 'Working Day'])
    #print(cal.holidays_index())
    #print(cal.bdays_count().sum()*9)
    
    # SQLAlchemy ORM conversion to pandas DataFrame