import calendar
from datetime import datetime

# Primeiro dia do m�s atual
PRIMEIRO_DIA_MES = str(1)

# �ltimo dia do m�s atual
ULTIMO_DIA_MES = str(calendar.monthrange(datetime.now().year, datetime.now().month)[1])

tasks = [

    {
    'text': 'element_1',
    'region': (425, 370, 466, 232),
    'delay': 1,
    'occurrence': 1,
    'char_type': 'letters',
    'backtrack': True
    }
]
