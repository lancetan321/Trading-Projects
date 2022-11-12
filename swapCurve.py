import pandas as pd
from numpy import log
from math import e
from scipy.interpolate import interp1d
import datetime as dt
from matplotlib import pyplot as plt
import pandasql as ps

std_tenors = ['O/N', '1MO', '3MO', '6MO',
              '1YR', '2YR', '3YR', '4YR',
              '5YR', '7YR', '10YR']
std_market_rates = [3.36, 2.99, 3.473, 3.977,
                    4.4, 4.425, 4.850, 5.075,
                    5.175, 5.475, 5.65]


class swapCurve:
    global std_tenors
    global std_market_rates

    def __init__(self, *args):
        if len(args) == 0:
            print('No arguments found: Building default swap curve...')
            self._curve = pd.DataFrame({'Tenor': std_tenors, 'Market Rate': std_market_rates})
        elif len(args) == 1:
            self._curve = pd.read_excel(args[0])
            self._curve.columns.values[0] = 'Tenor'
            self._curve.columns.values[1] = 'Market Rate'
        else:
            raise ValueError('Too many arguments!')

        self._curve['Date at Tenor'] = self.compute_dot
        self._curve['Zero Rate'] = self.compute_zr
        self._curve['Discount'] = self.compute_disc
        print(self._curve)

    @property
    def compute_dot(self):
        now = dt.datetime.now().date()
        date_of_tenors = [now + dt.timedelta(1),
                          now + dt.timedelta(30),
                          now + dt.timedelta(90),
                          now + dt.timedelta(180),
                          now + dt.timedelta(365),
                          now + dt.timedelta(730),
                          now + dt.timedelta(1095),
                          now + dt.timedelta(1460),
                          now + dt.timedelta(1825),
                          now + dt.timedelta(2555),
                          now + dt.timedelta(3650),]
        return date_of_tenors

    @property
    def compute_zr(self):
        zero_rates = []
        for i in self._curve.index:
            market_rate = self._curve['Market Rate'][i] / 100.0
            if self._curve['Tenor'][i] == 'O/N':
                zero_rates.append(None)
            elif self._curve['Tenor'][i] == '1MO':
                zero_rates.append(round(12.0*log(1.0+market_rate*(1.0/12.0))*100.0, 3))
            elif self._curve['Tenor'][i] == '3MO':
                zero_rates.append(round(4.0*log(1.0+market_rate*(1.0/4.0))*100.0, 3))
            elif self._curve['Tenor'][i] == '6MO':
                zero_rates.append(round(2.0*log(1.0+market_rate*(1.0/2.0))*100.0, 3))
            else:
                zero_rates.append(round(4.0*log(1.0+market_rate*(1.0/4.0))*100.0, 3))
        return zero_rates

    @property
    def compute_disc(self):
        discounts = []
        for i in self._curve.index:
            zero_rate = self._curve['Zero Rate'][i] / 100.0
            if self._curve['Tenor'][i] == 'O/N':
                discounts.append(1.0)
            elif self._curve['Tenor'][i] == '1MO':
                discounts.append(round(1/(1+zero_rate*30.0/360.0), 3))
            elif self._curve['Tenor'][i] == '3MO':
                discounts.append(round(1/(1+zero_rate*90.0/360.0), 3))
            elif self._curve['Tenor'][i] == '6MO':
                discounts.append(round(1/(1+zero_rate*180.0/360.0), 3))
            else:
                discounts.append(round(1/(1+zero_rate*30/360)**i, 3))
        return discounts

    @property
    def visualize(self):
        dates_n_rates = self._curve[['Date at Tenor', 'Zero Rate']].copy()
        dates_n_rates.rename(columns={'Date at Tenor': 'dotnr', 'Zero Rate': 'zr'}, inplace=True)
        dates_n_rates.dropna(inplace=True)
        base = dt.datetime.today().date()
        dates_to_interp = pd.DataFrame({'dot': [base + dt.timedelta(days=x) for x in range(30, 3651)]})

        query = ''' SELECT dates_to_interp.dot, dates_n_rates.zr
                    FROM dates_to_interp
                    LEFT JOIN dates_n_rates ON dates_to_interp.dot = dates_n_rates.dotnr
                    ORDER BY dates_to_interp.dot'''
        to_interp_df = ps.sqldf(query).rename(columns={'dot': 'Date at Tenor', 'zr': 'Swap Rate'})

        to_interp_df.interpolate(method='linear', inplace=True)
        to_interp_df.plot(x='Date at Tenor', y='Swap Rate', xlabel='Date at Tenor', ylabel='Swap Rate', legend=False)
        plt.xticks(rotation=20)
        plt.show()

        print(to_interp_df)

    @property
    def price_swap(self, swap):
        pass

    @property
    def get_table(self):
        return self._curve

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    sc = swapCurve()
    sc.visualize



