import pandas as pd
import numpy as np
import datetime

class Bond:
    '''
    Initial class for bond initialization. Currently works only with simple vanilla bonds.
    Functionality:
    - sets payment periods for the current vanilla bond (as indexes)
    - sets payments for a vanilla bond, creating pd.Series
    '''
    def __init__(self, coupons: float, times_per_year: int, face_value: int,
                 issue_date: np.datetime64, redemption_date: np.datetime64):
        self.coupons = coupons # Coupon % to the face value
        self.times_per_year = times_per_year #How often coupons are paid per year
        self.face_value = face_value #Face value of the bond (for coupons and final payment
        self.issue_date = issue_date #Issua date of the bond
        self.redemption_date = redemption_date #Date of bond redemption

    def _set_payment_periods(self):
        '''
        The main objective is to create dates of future payments.

        :return: payments_dates: list of dates with payments. The first date is the issue date,
        so leave it for further notice

        '''
        months = pd.Timestamp(self.redemption_date).month - pd.Timestamp(self.issue_date).month
        years = pd.Timestamp(self.redemption_date).year - pd.Timestamp(self.issue_date).year
        number_of_months = years * 12 + months
        range_ = 0
        if self.times_per_year == 2:
            range_ = round(number_of_months/6)
        elif self.times_per_year == 4:
            range_ = round(number_of_months / 3)
        payments_dates = pd.date_range(start=self.issue_date,
                                       end=self.redemption_date,
                                       periods = range_)
        return payments_dates

    def _set_payments(self):
        '''

        :return: pd.Series - series with index of payment dates and values - amount of money
        '''
        indexes = self._set_payment_periods()[1:]
        coupon_money = np.ones(shape=len(indexes)) *((self.coupons * self.face_value) / 100 )
        coupon_money [-1] += self.face_value
        payments = pd.Series(index = indexes,
                             data= coupon_money)
        self.payments = payments
        return self


class Discount_Factor:
    '''
    A supporting class for Bond class, which main objective is to price a given vanilla bond.
    Functionality:
    - create discount factors on a given date
    - discount future CF of a given bond
    - calculate a fair theoretical price of the given bond with these rates
    '''
    def __init__(self,
                 rates: np.array,
                 date: datetime,
                 curr_bond: Bond):
        self.rates = rates # np.array of rates used to discount CF
        self.settlement_day = date #the date on which we need to discount CF of the bond
        self.bond = curr_bond # the bond which we want to price

    def discount_factors(self):
        '''

        A function to make discount factors of the bond, given at the moment of the class initialization

        :param self:
        :return: self
        '''
        payments = self.bond.payments
        powers = np.arange(1, len(payments))
        if self.bond.times_per_year == 2:
            big_t = 181
        elif self.bond.times_per_year == 4:
            big_t = 90
        else:
            raise NotImplementedError('You have not done it yet')
        small_t = pd.Timestamp(payments.index[0]).day - pd.Timestamp(self.settlement_day).day
        drob = small_t / big_t
        powers = powers - drob
        self.powers = powers
        first_part = 1 + self.rates
        first_part = 1 / first_part
        discount_factors = first_part ** self.powers
        self.discount_factors = discount_factors
        return self

    def discount_payments(self):
        '''

        Create final np.array of discounted payments for the bond.

        :param self:
        :return: self
        '''
        self.discounted_payments = self.bond.payments / self.discounted_payments
        return self

    def price_bond(self):
        '''
        
        Price the given bond

        :return: fair_price of the vanilla bond
        '''
        return np.sum(self.discounted_payments)

