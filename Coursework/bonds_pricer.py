import pandas as pd
import numpy as np
import datetime
from scipy.interpolate import interp1d
import json



class Bond:
    '''
    Initial class for bond initialization. Currently works only with simple vanilla bonds.
    Functionality:
    - sets payment periods for the current vanilla bond (as indexes)
    - sets payments for a vanilla bond, creating pd.Series
    '''

    def __init__(self, coupons: float, times_per_year: int, face_value: int,
                 issue_date: np.datetime64, redemption_date: np.datetime64,
                 payments: pd.Series):
        self.coupons = coupons  # Coupon % to the face value
        self.times_per_year = times_per_year  # How often coupons are paid per year
        self.face_value = face_value  # Face value of the bond (for coupons and final payment
        self.issue_date = issue_date  # Issua date of the bond
        self.redemption_date = redemption_date  # Date of bond redemption
        self.payments = payments
        self.one_period = payments.index.to_series().diff()[1].days

    ''' ОСТАТОК ОТ ПЕРВОЙ РЕАЛИЗАЦИИ
    def _set_payment_periods(self):

        The main objective is to create dates of future payments.

        :return: payments_dates: list of dates with payments. The first date is the issue date,
        so leave it for further notice


        months = pd.Timestamp(self.redemption_date).month - pd.Timestamp(self.issue_date).month
        years = pd.Timestamp(self.redemption_date).year - pd.Timestamp(self.issue_date).year
        number_of_months = years * 12 + months
        range_ = 0
        if self.times_per_year == 2:
            range_ = round(number_of_months / 6) + 1
        elif self.times_per_year == 4:
            range_ = round(number_of_months / 3) + 1
        payments_dates = pd.date_range(start=self.issue_date,
                                       end=self.redemption_date,
                                       periods=range_)
        self.one_period = payments_dates.to_series().diff()[1].days
        return payments_dates
    '''

    '''
    def set_payments(self):


        :return: pd.Series - series with index of payment dates and values - amount of money

        indexes = self._set_payment_periods()[1:]
        coupon_money = np.ones(shape=len(indexes)) * ((self.coupons * self.face_value) / 100) / self.times_per_year
        coupon_money[-1] += self.face_value
        payments = pd.Series(index=indexes,
                             data=coupon_money)
        self.payments = payments
        return self
    '''


class Discount_Factor:
    '''
    A supporting class for Bond class, which main objective is to price a given vanilla bond.
    Functionality:
    - create discount factors on a given date
    - discount future CF of a given bond
    - calculate a fair theoretical price of the given bond with these rates
    '''

    def __init__(self,
                 rates: pd.Series,
                 date: datetime,
                 curr_bond: Bond,
                 payment: float):
        self.rates = rates.dropna()  # pd.Series of rates used to discount CF (index - years, values - rates)
        self.settlement_day = date  # the date on which we need to discount CF of the bond
        self.bond = curr_bond  # the bond which we want to price
        self.payment_for_1_period = payment

    def discount_factors(self):
        '''

        A function to make discount factors of the bond, given at the moment of the class initialization

        :param self:
        :return: self
        '''
        payments = self.bond.payments
        indexes = self.bond.payments.index
        len_right = len(indexes[indexes > pd.to_datetime(self.settlement_day)])
        init_len = len(self.bond.payments)
        self.bond.payments = payments[init_len - len_right:]
        if self.bond.times_per_year == 2:
            self.big_t = 181
        elif self.bond.times_per_year == 4:
            self.big_t = 90
        else:
            raise NotImplementedError('You have not done it yet')
        days_ = pd.DataFrame(columns=['now', 'payments'])
        now_l = [self.settlement_day for _ in range(len(self.bond.payments))]
        days_.now = now_l
        days_.payments = self.bond.payments.index
        days_.payments = pd.to_datetime(days_.payments)
        days_.now = pd.to_datetime(days_.now)
        self.diff_in_days = (days_.payments - days_.now)
        self.t = self.diff_in_days / datetime.timedelta(
            days=365)  # временной отрезок в годах, на котором мы сейчас находимся (pd.Series)
        interpolation = interp1d(x=self.rates.index,
                                 y=self.rates.values)
        rates_to_discount = []
        for value in self.t.values:
            try:
                rates_to_discount.append(interpolation(value))
            except ValueError:
                rates_to_discount.append(self.rates.values[-1])
                '''
                если выходим за грань интерполяции - например, очень длинный бонд, а ставки дисконтрования только на 10 лет
                то предполагаем, что они будут равны самой последней
                '''
        rates_to_discount = np.array(rates_to_discount)
        rates_to_discount = (1.0 + rates_to_discount) ** np.array(self.t.values, dtype='float64')
        discount_factors = 1 / rates_to_discount
        self.discount_factors = discount_factors
        return self

    def discount_payments(self):
        '''

        Create final np.array of discounted payments for the bond.

        :param self:
        :return: self
        '''
        self.discounted_payments = self.bond.payments * self.discount_factors
        return self

    def price_bond(self):
        '''

        Price the given bond

        :return: fair_price of the vanilla bond
        '''
        self.discount_factors()
        self.discount_payments()
        day_now = (self.diff_in_days / datetime.timedelta(days=1)).values[0]
        accrued = self.payment_for_1_period * (self.bond.one_period - day_now) / self.bond.one_period
        return np.sum(self.discounted_payments) - accrued

