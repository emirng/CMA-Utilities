import datetime


def date_output(date_str):
    if date_str is None:
        return '-'
    if not type(date_str) == str:
        raise ValueError()
    dt = datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%f%z')
    return dt.strftime('%Y-%m-%d<br>%H:%M %z')
