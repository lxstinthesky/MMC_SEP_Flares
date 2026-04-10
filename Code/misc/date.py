import datetime


def next_date(current_date):
    '''
    Computes next date depending on current date. This takes into account that months do not all have the same amount of days and includes leap years.
    
    parameters:
    current_date: string of current date (yyyy-mm-dd)
    '''
    current = datetime.datetime.strptime(current_date, "%Y-%m-%d").date()
    current += datetime.timedelta(days=1)
    
    return str(current)

def previous_date(current_date):
    '''
    Computes previous date depending on current date. This takes into account that months do not all have the same amount of days and includes leap years.
    
    parameters:
    current_date: string of current date (yyyy-mm-dd)
    '''
    current = datetime.datetime.strptime(current_date, "%Y-%m-%d").date()
    current -= datetime.timedelta(days=1)
    
    return str(current)


def parse_date_list(utc_times: list[str]):
    return [datetime.datetime.fromisoformat(utc_time) for utc_time in utc_times]


def utc_to_datetime(utc):
    return datetime.datetime.strptime(utc[2:10] + " " + utc[11:19], "%y-%m-%d %H:%M:%S")