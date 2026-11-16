import pandas as pd
from pandas import DataFrame
import datetime as dt
import numpy as np

from models import TA, Dates_Interval



class Data_Calculation():
    def __init__(self, 
                 resps_fp: str = './raw_data/respondents.csv',
                 views_fp: str = './raw_data/views.csv'):
        
        self.views_df = pd.read_csv(views_fp,
                                 parse_dates=['date'],
                                 dayfirst=True)
        
        self.resps_df = pd.read_csv(resps_fp,
                      parse_dates=['birth_date'],
                      dayfirst=True)

        self.resps_df['age'] = dt.datetime.now().year - self.resps_df['birth_date'].dt.year

    def __add_correct_age(self, dates: Dates_Interval):
        '''Добавляем в df респондентов их возраст относительно последнего дня последнего месяца правого конца интервала дат'''
        age_years = dates.finish.year - self.resps_df['birth_date'].dt.year
        year_mask = (dates.finish.month < self.resps_df['birth_date'].dt.month) | (
            (dates.finish.month == self.resps_df['birth_date'].dt.month) & (dates.finish.day < self.resps_df['birth_date'].dt.day))

        self.resps_df['age'] = np.where(year_mask, age_years - 1, age_years)

    def __get_target_aud(self, target: TA, dates: Dates_Interval) -> DataFrame:
        """По критериям таргета формируем фрейм с подходящей аудиторией"""
        self.__add_correct_age(dates)
        mask = (self.resps_df['age'] >= target.min_age) & \
                (self.resps_df['age'] <= target.max_age)
        if target.gender.value != 'ALL':
            mask = mask & (target.gender.value == self.resps_df['gender'])
        if target.income_group is not None:
            mask = mask & (self.resps_df['income_group'].isin(list(target.income_group.value)))
        return(self.resps_df[mask])

    def __get_intime_views(self, dates: Dates_Interval) -> DataFrame:
        """возвращаем фрейм только с теми просмотрами, которые попали в заданный 
        интервал времени"""
        start = pd.Timestamp(dates.start)
        fin = pd.Timestamp(dates.finish)
        mask = self.views_df['date'].between(start, fin)
        return self.views_df[mask]

    def __top_advertisers_by_reach(self, intime_views_df: DataFrame, target_aud_df: DataFrame) -> DataFrame:
        """расчитываем нисходящий топ рекламодателей по охвату в заданном диапазоне ЦЕЛЕВЫХ ПРОСМОТРОВ"""
        targ_views = pd.merge(left = intime_views_df, right = target_aud_df,
                              left_on = 'respondent_id', right_on = 'id', how = 'left')
        ta_amount = len(target_aud_df)

        # удаляем повторные просмотры
        targ_views = targ_views.drop_duplicates(subset=['ad_id', 'respondent_id'])

        # считаем общее количество роликов для каждого рекламодателя
        targ_views['unique_ad_amount'] = targ_views.groupby('advertiser')['ad_id'].transform('nunique')

        # считаем количество просмотров ЦА для каждого ролика
        targ_views = targ_views.groupby(['advertiser', 'ad_id', 'unique_ad_amount']).agg(
            ta_views = ('id_y', 'count')
        ).reset_index()

        # считаем охват
        targ_views['ad_reach'] = targ_views['ta_views'] / ta_amount

        # считаем суммарный охват
        targ_views = targ_views.groupby(['advertiser', 'unique_ad_amount']).agg(
            total_reach = ('ad_reach', 'sum')
        ).reset_index()

        # находим среднее по охвату по всем ролкиам
        targ_views['avg_reach'] = targ_views['total_reach'] / targ_views['unique_ad_amount']

        # input(targ_views.sort_values('avg_reach', ascending=False).head(10))
        return(targ_views.sort_values('avg_reach', ascending=False))

    def _trp_within_period_by_months(self, advertisers: list[str], 
                                     targ_aud_df: DataFrame,
                                     intime_views_df: DataFrame):
        """По ЦА и просмотрам, попадающим в заданный период считаем trp по месяцам за заданный период для заданных рекламодателей"""
        ta_amount = len(targ_aud_df)

        # выкидываем просмотры от тех рекламодателей, который не входятв наш список
        intime_views_df = intime_views_df[intime_views_df['advertiser'].isin(advertisers)]

        # находим все целевые просмотры
        target_views_df = pd.merge(left=intime_views_df, right=targ_aud_df, how='inner',
                    left_on='respondent_id', right_on='id')

        # input(target_views_df)
        # input(target_views_df.columns)

        # для группировки по месяцам 
        window = pd.Grouper(key='date', freq='ME')

        # считаем общее количество просмотров целевой аудиторией (id_y это id из правой (respondents) таблички)
        target_views_df = target_views_df.groupby([window, 'advertiser']).agg(
            total_views = ('id_y', 'count')).reset_index()
        # print()

        # считаем итоговый trp по каждому рекламодателю в рамках месяц
        target_views_df['ad_trp'] = target_views_df['total_views'] / ta_amount * 100
        return target_views_df
        ...        

    def _calcs(self, target: TA, dates: Dates_Interval) -> list[str]:
        """Считаем средний охват по рекламодателям за период и возвращаем наименования топ-5"""
        #получаем фрейм просмотров в нужный период и фрейм с ЦА из всей аудитории
        targ_aud_df = self.__get_target_aud(target, dates)
        intime_views_df = self.__get_intime_views(dates)

        # берем топ5 рекламодателей по среднему охвату
        advertisers = self.__top_advertisers_by_reach(intime_views_df, targ_aud_df)['advertiser'].head(5).tolist()
        # считаем для них трп по месяцам за период
        trp_adv_monthly = self._trp_within_period_by_months(advertisers, targ_aud_df, intime_views_df)
        return(advertisers, trp_adv_monthly.head(5))
        # return advertisers


if __name__ == "__main__":
    a = Data_Calculation()
    target = TA(gender='M', min_age = 25, max_age = 40, income_group='B')
    dates = Dates_Interval(start=dt.datetime(year=2024, month=1, day=1), finish=dt.datetime(year=2026, month=6, day=30))

    # print(a._top5_advertisers_by_reach(targ_aud, dates))
    print(a._calcs(target, dates))