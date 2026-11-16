import sys 
from pydantic import ValidationError
import datetime as dt



from models import TA, Dates_Interval
from data_proc import Data_Calculation



def parse_ta(ta: str) -> TA:
    ta = ta.split('_')
    ta_proc = dict()

    ta_proc['gender'] = ta[0]
    
    if ta[1][-1] == '+':
        ta_proc['min_age'] = float(ta[1][:-1])
    else:
        ta_proc['min_age'] = float(ta[1])
        ta_proc['max_age'] = float(ta[2])
        if ta_proc['max_age'] < ta_proc['min_age']:
            print('Диапазон возрастов задан некорректно')
            raise ValidationError
    if ta[-1].isalpha():
        ta_proc['income_group'] = ta[-1]
    else:
        ta_proc['income_group'] = None

    return TA(**ta_proc)

def parse_date(start: str, finish: str) -> Dates_Interval:
    try:
        start = dt.datetime.strptime(start, '%m.%Y')
        finish = dt.datetime.strptime(finish, '%m.%Y')

        next_month = finish.month % 12 + 1
        next_year = finish.year + 1
        finish = dt.datetime(year=next_year, month=next_month, day=1) - dt.timedelta(days=1)

        if start > finish: 
            raise NameError
        return Dates_Interval(start=start, finish=finish)
    except ValueError:
        raise ValidationError
    except NameError:
        print('Начальная дата не может быть позже конечной даты')
        raise ValidationError

def check_filepath(filepath:str) -> str:
    try:
        _, format = filepath.split('.')

        if format != 'pptx':
            print('Некорректный формат презентации')
            raise ValidationError
        with open(filepath, 'w') as f:
            pass
        return filepath
    
    except OSError:
        print('Некорректный файловый путь')
        raise ValidationError

user_inp = sys.argv[1:]
try:
    # input(user_inp)
    ta, start, finish, filepath = user_inp
    targ_aud = parse_ta(ta)
    dates = parse_date(start, finish)
    filepath = check_filepath(filepath)
    input(dates)
    input(targ_aud)
    a = Data_Calculation()._calcs(targ_aud, dates)
    print(a)
except ValidationError:
    print('Некорректные параметры запуска')
except Exception:
    print("Ошибка ввода даты")






