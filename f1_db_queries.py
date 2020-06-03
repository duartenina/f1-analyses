import yaml
import mysql.connector as sql
import pandas as pd


DEFAULT_COLS = """
, `year`
, round
, races.name as raceName
, circuits.circuitRef
, drivers.forename
, drivers.surname
, constructorId
, constructors.name as constructorName
, constructors.constructorRef
"""

TABLES_TO_JOIN = """
join races using (raceId)
join constructors using (constructorId)
join drivers using (driverId)
join circuits using (circuitId)
"""

COND_FASTEST_LAPS = "results.rank = 1"
COND_RACE_WINNERS = "results.position = 1"
COND_POLE_POSITION = "qualifying.position = 1"


def connect_to_db():
    with open('mysql_info.yaml', 'r') as f:
        db_info = yaml.load(f.read(), Loader=yaml.SafeLoader)

    database = sql.connect(
        host='localhost',
        user=db_info['user'],
        passwd=db_info['passwd'],
        database='sys'
    )
    cursor = database.cursor()

    return database, cursor


# https://code.tutsplus.com/articles/sql-for-beginners-part-2--net-8274
# https://code.tutsplus.com/articles/sql-for-beginners-part-3-database-relationships--net-8561
def run_query(cursor, query_str, return_pandas=True, pandas_col_index='resultId'):
    try:
        cursor.execute(query_str)
    except sql.InternalError:
        cursor.fetchall()
        cursor.execute(query_str)

    rows = cursor.fetchall()

    if return_pandas:
        df = pd.DataFrame(rows, columns=cursor.column_names)
        if pandas_col_index is not None:
            df.set_index(pandas_col_index, inplace=True)
        return df
    else:
        return rows


def run_query_generic(cursor, condition, cols=None, tables=None,
                      order_by='`year`', col_index=None):

    if cols is None:
        cols = 'resultId' + DEFAULT_COLS

    if tables is None:
        table = 'results' + TABLES_TO_JOIN

    if col_index is None:
        col_index = 'resultId'

    query_str = (
        ' select ' + cols + ' from ' + tables
        + ' where ' + condition
        + ' order by ' + order_by
    )
    # print(query_str)
    return run_query(cursor, query_str, pandas_col_index=col_index)


def run_query_results(cursor, condition):
    cols = 'resultId' + DEFAULT_COLS
    tables = 'results' + TABLES_TO_JOIN

    query_str = (
        ' select ' + cols + ' from ' + tables
        + ' where ' + condition
        + ' order by ' + '`year`'
    )
    # print(query_str)
    return run_query(cursor, query_str, pandas_col_index='resultId')


def run_query_qualifying(cursor, condition):
    cols = 'qualifyId' + DEFAULT_COLS
    tables = 'qualifying' + TABLES_TO_JOIN

    query_str = (
        ' select ' + cols + ' from ' + tables
        + ' where ' + condition
        + ' order by ' + '`year`'
    )
    # print(query_str)
    return run_query(cursor, query_str, pandas_col_index='qualifyId')


def get_constructors_info(cursor):
    query_str = 'select constructorId, constructorRef, name from constructors'

    constructors_df = run_query(cursor, query_str,
                                pandas_col_index='constructorId')

    constructors_df['parent'] = ''

    # Fix Lotus
    lotus_ind = constructors_df['constructorRef'] == 'team_lotus'
    constructors_df.loc[lotus_ind, 'constructorRef'] = 'lotus'
    constructors_df.loc[lotus_ind, 'name'] = 'Lotus'

    team_ref = constructors_df['constructorRef']
    constructors_df['parent'] = team_ref.str.split('-', n=1, expand=True)

    last_index = constructors_df.index.max()
    constructors_df.loc[last_index + 1] = [
        'indy500', 'Indianapolis 500', 'indy500'
    ]

    return constructors_df