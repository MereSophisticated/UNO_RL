from datetime import datetime
COLORS = 4


def get_timestamp():
    return datetime.now().strftime('%Y-%m-%d_%H-%M')

