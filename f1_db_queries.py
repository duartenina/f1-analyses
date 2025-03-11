import yaml
import mariadb as sql
import pandas as pd


DEFAULT_COLS = """
, `year`
, round
, races.name as raceName
, circuits.circuitRef
, driverId
, drivers.forename
, drivers.surname
, drivers.driverRef
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

    database_connection = sql.connect(
        host='localhost',
        user=db_info['user'],
        passwd=db_info['passwd'],
        database=db_info['database']
    )

    return database_connection


# https://code.tutsplus.com/articles/sql-for-beginners-part-2--net-8274
# https://code.tutsplus.com/articles/sql-for-beginners-part-3-database-relationships--net-8561
def run_query(db_conn, query_str, return_pandas=True, col_index='resultId'):
    try:
        return run_query_no_catch(db_conn, query_str, return_pandas, col_index)
    except Exception:
        print("QUERY ERROR")
        print(query_str)

        return None

def run_query_no_catch(db_conn, query_str, return_pandas=True, col_index='resultId'):
    if return_pandas:
        df = pd.read_sql(query_str, db_conn)
        if col_index is not None:
            df.set_index(col_index, inplace=True)

        return df

    try:
        db_conn.cursor.execute(query_str)
    except sql.InternalError:
        db_conn.cursor.fetchall()
        db_conn.cursor.execute(query_str)

    rows = db_conn.cursor.fetchall()
    return rows


def run_query_generic(db_conn, condition, cols=None, tables=None,
                      order_by='`year`', col_index='raceId'):
    if cols is None:
        cols = 'resultId' + DEFAULT_COLS

    if tables is None:
        table = 'results' + TABLES_TO_JOIN

    # if col_index is None:
    #     col_index = 'resultId'

    query_str = ' select ' + cols + ' from ' + tables
    if condition is not None:
        query_str += ' where ' + condition

    if order_by is not None:
        query_str += ' order by ' + order_by

    # print(query_str)
    return run_query(db_conn, query_str, col_index=col_index)


def run_query_results(db_conn, condition):
    cols = 'raceId' + DEFAULT_COLS + ', points'
    tables = 'results' + TABLES_TO_JOIN

    return run_query_generic(
        db_conn, condition=condition,
        cols=cols, tables=tables, order_by='`year`', col_index='raceId'
    )


def run_query_qualifying(db_conn, condition):
    cols = 'raceId' + DEFAULT_COLS
    tables = 'qualifying' + TABLES_TO_JOIN

    return run_query_generic(
        db_conn, condition=condition,
        cols=cols, tables=tables, order_by='`year`', col_index='raceId'
    )


def run_query_max_points(db_conn):
    cols = 'r1.raceId' + DEFAULT_COLS
    table_max_points = (
        '(select resultId, raceId, constructorId, driverId, sum(points) as sp'
        ' from results group by raceId, constructorId)'
    )
    tables = (
        table_max_points + ' as r1' +
        TABLES_TO_JOIN +
        ' inner join ('
            'select resultId, raceId, max(sp) as sp'
            ' from ' + table_max_points + ' as rt'
            ' group by raceId order by sp'
        ') as r2'
        ' on (r1.raceId = r2.raceId and r1.sp = r2.sp)'
    )

    return run_query_generic(
        db_conn, condition=None,
        cols=cols, tables=tables, order_by='`year`', col_index='raceId'
    )


def get_constructors_info(db_conn):
    query_str = 'select constructorId, constructorRef, name from constructors'

    constructors_df = run_query(db_conn, query_str,
                                col_index='constructorId')

    constructors_df['parent'] = ''

    # Fix Lotus
    lotus_ind = constructors_df['constructorRef'] == 'team_lotus'
    constructors_df.loc[lotus_ind, 'constructorRef'] = 'lotus'
    constructors_df.loc[lotus_ind, 'name'] = 'Lotus'

    # Add parent team (ignore engine manufacturers, etc)
    team_ref = constructors_df['constructorRef']
    constructors_df['parent'] = team_ref.str.split('-', expand=True)[0]     # we only want the first column ('0') of the split

    # add fake constructor for Indy 500 races
    last_index = constructors_df.index.max()
    constructors_df.loc[last_index + 1] = [
        'indy500', 'Indianapolis 500', 'indy500'
    ]
    constructors_df.loc[last_index + 2] = [
        'emptyOrange', 'Empty Orange', 'emptyOrange'
    ]
    constructors_df.loc[last_index + 3] = [
        'emptyBrown', 'Empty Brown', 'emptyBrown'
    ]

    return constructors_df


def get_drivers_info(db_conn):
    query_str = 'select driverId, driverRef, forename, surname from drivers'

    drivers_df = run_query(db_conn, query_str, col_index='driverId')

    # name is first letter of forename and surname, e.g., L. Hamilton
    drivers_df['name'] = (
        drivers_df['forename'].str[0] + '. ' + drivers_df['surname']
    )

    return drivers_df


def get_champions(db_conn):
    cols = 'mround.year as `year`, {standings_id}'
    tables = (
        '(select `year`, max(round) as finalRound'
            ' from races group by `year` order by `year`) as mround'
        ' inner join races on '
            '(races.`year` = mround.year and races.round = mround.finalRound)'
        ' join {standings_table} using (raceId)'
    )
    cond = '{standings_table}.position = 1'

    wdc = run_query_generic(
        db_conn, condition=cond.format(standings_table='driverStandings'),
        cols=cols.format(standings_id='driverId'),
        tables=tables.format(standings_table='driverStandings'),
        col_index='year'
    )
    wcc = run_query_generic(
        db_conn, condition=cond.format(standings_table='constructorStandings'),
        cols=cols.format(standings_id='constructorId'),
        tables=tables.format(standings_table='constructorStandings'),
        col_index='year'
    )

    champs = {
        'wdc': wdc,
        'wcc': wcc
    }

    return champs


def get_seasons_participated(db_conn, team='ferrari'):
    years = run_query(
        db_conn,
        f"""
        SELECT DISTINCT `year`
        FROM results
        JOIN constructors USING (constructorId)
        JOIN races USING (raceId)
        WHERE constructorRef = '{team}'
        """
    )

    return years.to_numpy()


def get_wins_per_team_per_year(db_conn):
    df = run_query(
        db_conn,
        """
        SELECT `constructorRef`, `year`, COUNT(*) AS `wins`
        FROM results
        JOIN constructors USING (constructorId)
        JOIN races USING (raceId)
        WHERE `position` = 1
        GROUP BY `constructorRef`, `year`
        """,
        col_index=None
    )

    return df


def get_team_with_most_wins_per_year(db_conn):
    df = run_query(
        db_conn,
        """
        SELECT t.`year`, t.`constructorRef`, MAX(t.`wins`) as `max_wins`
        FROM (
            SELECT `constructorRef`, `year`, COUNT(*) AS `wins`
                FROM results
                JOIN constructors USING (constructorId)
                JOIN races USING (raceId)
                WHERE `position` = 1
                GROUP BY `constructorRef`, `year`
                ORDER BY `year` DESC, `wins` DESC
        ) AS t
        GROUP BY `year`
        ORDER BY `year` DESC
        """
    )

    return df

def get_driver_with_most_wins_per_year(db_conn):
    df = run_query(
        db_conn,
        """
        SELECT t.`year`, t.`driverRef`, MAX(t.`wins`) as `max_wins`
        FROM (
            SELECT `driverRef`, `year`, COUNT(*) AS `wins`
                FROM results
                JOIN drivers USING (driverId)
                JOIN races USING (raceId)
                WHERE `position` = 1
                GROUP BY `driverRef`, `year`
                ORDER BY `year` DESC, `wins` DESC
        ) AS t
        GROUP BY `year`
        ORDER BY `year` DESC
        """
    )

    return df
