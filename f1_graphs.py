import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.gridspec import GridSpec
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from f1_api import get_all_race_winners, get_seasons_team


TEAM_COLORS = {
    'ferrari': ('red', 'red'),
    'mclaren': ('orange', 'orange'),
    'williams': ('grey', 'grey'),
    'mercedes': ('aqua', 'aqua'),
    'lotus': ('black', 'gold'),
    'red_bull': ('darkblue', 'darkblue'),
    'brabham': ('black', 'white'),
    # 'renault': ('black', 'orange'),
    'renault': ('deepskyblue', 'yellow'),
    'benetton': ('green', 'green'),
    'tyrrell': ('blue', 'white'),
    'brm': ('darkgreen', 'white'),
    'cooper': ('darkblue', 'cyan'),
    'alfa': ('red', 'white'),
    'vanwall': ('green', 'gold'),
    'ligier': ('lightblue', 'black'),
    'maserati': ('red', 'black'),
    'matra': ('cyan', 'black'),
    'brawn': ('grey', 'yellow'),
    'march': ('orange', 'black'),
    'jordan': ('yellow', 'black'),
    'honda': ('white', 'red'),
    'wolf': ('black', 'cyan'),
    'lotus_f1': ('black', 'red'),
    'toro_rosso': ('darkblue', 'grey'),
    'bmw_sauber': ('white', 'blue'),
    'stewart': ('white', 'green'),
    'porsche': ('bisque', 'gold'),
    'eagle': ('blue', 'red'),
    'hesketh': ('brown', 'blue'),
    'penske': ('pink', 'cyan'),
    'shadow': ('darkgrey', 'brown'),
    'force_india': ('pink', 'pink'),
    'racing_point': ('pink', 'black'),
    'toyota': ('lightgrey', 'red'),
    'sauber': ('firebrick', 'white'),
    'bar': ('darkgoldenrod', 'red'),
    'haas': ('darkgoldenrod', 'black'),
    'indy500': ('white', 'grey'),
    'others': ('black',)*2,
    'emptyOrange': ('peru',)*2,
    'emptyBrown': ('brown',)*2,
}
DRIVER_COLORS = {
    'fangio': 'black',
    'jack_brabham': 'cyan',
    'clark': 'yellow',
    'stewart': 'black',
    'lauda': 'blue',
    'piquet': 'yellow',
    'prost': 'white',
    'senna': 'cyan',
    'michael_schumacher': 'black',
    'alonso': 'white',
    'raikkonen': 'cyan',
    'vettel': 'yellow',
    'hamilton': 'blue',
}
MAX_RACES_YEAR = 21
F1_FIRST_YEAR = 1950
F1_LATEST_YEAR = 2019


def parse_dataframe(races_df_base, constructors_df, champions_df):
    num_years = F1_LATEST_YEAR - F1_FIRST_YEAR + 1

    races_df = races_df_base.copy(deep=True)
    team_results = np.zeros((num_years, MAX_RACES_YEAR), dtype='u4')
    driver_results = np.zeros((num_years, MAX_RACES_YEAR), dtype='u4')

    race_year_ind = races_df['year'] - F1_FIRST_YEAR
    race_round_ind = races_df['round'] - 1
    indy500_races = races_df['raceName'] == 'Indianapolis 500'

    # Fix Indy 500 winners
    races_df.loc[indy500_races, 'constructorId'] = constructors_df[
        constructors_df['constructorRef'] == 'indy500'
    ].index[0]

    # Add results to numpy tables
    team_results[race_year_ind, race_round_ind] = races_df['constructorId']
    driver_results[race_year_ind, race_round_ind] = races_df['driverId']

    # Get teams/drivers with most wins in a year
    races_years = races_df_base.groupby('year')
    got_most_wins = lambda r: r.value_counts().index[0]

    team_most_wins = races_years['constructorId'].agg(got_most_wins)
    driver_most_wins = races_years['driverId'].agg(got_most_wins)

    team_most_wins = team_most_wins.to_numpy().reshape((-1, 1))
    driver_most_wins = driver_most_wins.to_numpy().reshape((-1, 1))

    # Fix WCC only starting in 1958
    for year in range(F1_FIRST_YEAR, F1_LATEST_YEAR + 1):
        if year in champions_df['wcc'].index:
            continue

        champions_df['wcc'].loc[year] = 0

    champions_df['wcc'].sort_index(inplace=True)

    # Join everything
    white_col = np.zeros((F1_LATEST_YEAR - F1_FIRST_YEAR + 1, 1), dtype='u4')
    color_col = np.ones((F1_LATEST_YEAR - F1_FIRST_YEAR + 1, 1), dtype='u4')
    orange_col = (
        color_col *
        constructors_df[constructors_df['constructorRef'] == 'emptyOrange'].index[0]
    )
    brown_col = (
        color_col *
        constructors_df[constructors_df['constructorRef'] == 'emptyBrown'].index[0]
    )

    team_results = np.hstack((
        team_results,
        white_col, white_col,
        champions_df['wcc'].to_numpy(),
        team_most_wins,
        white_col,
        brown_col,
        orange_col
    ))
    driver_results = np.hstack((
        driver_results,
        white_col, white_col,
        white_col,
        white_col,
        white_col,
        champions_df['wdc'].to_numpy(),
        driver_most_wins
    ))

    return {'team': team_results, 'driver': driver_results}


def plot_results_year_round_team_color(results, constructors_df, drivers_df,
                                       win_type='race',
                                       result_type='Race Wins'):
    fig = plt.figure(figsize=(8.1, 9))
    gs = GridSpec(1, 3, width_ratios=[1.3, 0.4, 0.4], wspace=0.1)

    team_results = results['team']
    driver_results = results['driver']

    color_names_sq = np.array(
        ['white'] * (constructors_df.index.max() + 1), dtype='U16'
    )
    color_names_sq[constructors_df.index] = constructors_df['parent'].apply(
        lambda t: TEAM_COLORS.get(t, TEAM_COLORS['others'])[0]
    )
    # print(color_names_sq[131])

    cmap_sq = ListedColormap(color_names_sq)

    # Plot
    ax_results = plt.subplot(gs[0])
    # ax_results_right = ax_results.twinx()
    ax_team_legend = plt.subplot(gs[1])
    ax_driver_legend = plt.subplot(gs[2])

    xlims = (0.5, team_results.shape[1] + 0.5)
    ylims = (F1_LATEST_YEAR + 0.5, F1_FIRST_YEAR - 0.5)

    # Races
    handles_team = []
    labels_team = []
    handles_driver = []
    labels_driver = []
    total_races = np.sum(team_results != 0)
    remaining_races = total_races

    ax_results.imshow(
        team_results, cmap=cmap_sq, vmin=0, vmax=constructors_df.index.max(),
        extent=(*xlims, *ylims)
    )

    team_ref_view = constructors_df.set_index('constructorRef')
    driver_ref_view = drivers_df.set_index('driverRef')

    team_n_races = []
    for n, team_id in enumerate(TEAM_COLORS):
        if team_id == 'others':
            name = 'Others'
            team_ids = constructors_df[
                ~constructors_df['parent'].isin(TEAM_COLORS)
            ].index
        else:
            name = team_ref_view.loc[team_id]['name']
            team_ids = constructors_df[constructors_df['parent'] == team_id].index

        race_wins = np.isin(team_results, team_ids)

        wins = np.sum(race_wins[:, :MAX_RACES_YEAR])
        y, x = np.nonzero(race_wins)
        x += 1          # shift round #
        y += 1950       # shift year

        if wins == 0:
            continue

        colors = TEAM_COLORS[team_id]
        if wins == 1:
            wins_label = f'{wins} {win_type}'
        else:
            wins_label = f'{wins} {win_type}s'
        label = f'{name} ({wins_label})'

        team_n_races.append((n, team_id, wins))

        h1, = ax_results.plot(np.nan, 's', ms=7, color=colors[0])
        h2, = ax_results.plot(x, y, 'o', ms=2, color=colors[1])

        handles_team.append((h1, h2))
        labels_team.append(label)

    driver_n_races = []
    for n, driver_ref in enumerate(DRIVER_COLORS):
        name = driver_ref_view.loc[driver_ref]['name']
        driver_ids = drivers_df[drivers_df['driverRef'] == driver_ref].index

        race_wins = np.isin(driver_results, driver_ids)

        wins = np.sum(race_wins[:, :MAX_RACES_YEAR])
        y, x = np.nonzero(race_wins)
        x += 1          # shift round #
        y += 1950       # shift year

        if wins == 0:
            continue

        color = DRIVER_COLORS[driver_ref]
        if wins == 1:
            wins_label = f'{wins} {win_type}'
        else:
            wins_label = f'{wins} {win_type}s'

        first_year = min(y)
        last_year = max(y)

        label = f'{name}\n{first_year}-{last_year}\n({wins_label})'

        driver_n_races.append((n, driver_ref, wins))

        h, = ax_results.plot(x, y, 's', ms=6, color=color,
                             markeredgewidth=1,
                             markerfacecolor='none')

        handles_driver.append(h)
        labels_driver.append(label)

    team_n_races = np.array(team_n_races, dtype=('u4,U16,u4'))
    driver_n_races = np.array(driver_n_races, dtype=('u4,U16,u4'))
    order_team = np.hstack((
        np.argsort(team_n_races[
            ~np.isin(team_n_races['f1'], ['indy500', 'others'])
        ]['f2'])[::-1],
        np.nonzero(team_n_races['f1'] == 'indy500')[0],
        np.nonzero(team_n_races['f1'] == 'others')[0],
    ))
    order_driver = np.argsort(driver_n_races['f2'])[::-1]

    # ax_results.axis('off')
    ax_results.invert_yaxis()

    # ax_results.invert_yaxis()

    ax_results.set_xticks([1] + [i for i in range(5, 21, 5)])
    ax_results.set_yticks(
        [ i for i in range(F1_FIRST_YEAR, F1_LATEST_YEAR, 5)] + [F1_LATEST_YEAR]
    )
    # ax_results_right.set_yticks(
    #     [ i for i in range(F1_FIRST_YEAR, F1_LATEST_YEAR, 5)] + [F1_LATEST_YEAR]
    # )

    ax_results.set_xlim(*xlims)
    ax_results.set_ylim(*ylims)
    # ax_results_right.set_ylim(*ylims)

    ax_results.set_xlabel('Race #')
    ax_results.set_ylabel('Year')
    # ax_results_right.set_ylabel('Year')

    # ax_results.axis('equal')
    # ax_results_right.axis('equal')

    # Champions
    ax_results.axvline(MAX_RACES_YEAR + 1.5, ls='--', color='k')

    last_col = team_results.shape[1]

    def add_line_label(x, y, label, ha='center', va='top', color='black'):
        signal = 1 if va == 'top' else -1

        line = mlines.Line2D(
            [x, x],
            [y + 1 * signal, y + 2 * signal],
            ls='-', color=color
        )
        line.set_clip_on(False)
        ax_results.add_line(line)

        ax_results.text(x, y + 2 * signal, label,
                        ha=ha, va=va, color=color)

    add_line_label(last_col - 4, F1_LATEST_YEAR, 'WCC ',
                   ha='center', va='top', color='cyan')
    add_line_label(last_col - 3, F1_FIRST_YEAR, 'Constructor\nwith most wins',
                   ha='right', va='bottom', color='blue')
    add_line_label(last_col - 1, F1_LATEST_YEAR, ' WDC',
                   ha='center', va='top', color='brown')
    add_line_label(last_col - 0, F1_FIRST_YEAR, 'Driver with\nmost wins',
                   ha='left', va='bottom', color='orange')

    # Team legend
    handles_team = [handles_team[n] for n in order_team]
    labels_team = [labels_team[n] for n in order_team]

    ax_team_legend.legend(handles_team, labels_team, loc='center',
                          facecolor=(.85, .85, .85))
    ax_team_legend.axis('off')

    # Driver legend
    # handles_driver = [handles_driver[n] for n in order_driver]
    # labels_driver = [labels_driver[n] for n in order_driver]

    ax_driver_legend.legend(handles_driver, labels_driver, loc='center',
                            facecolor=(.75, .75, .75))
    ax_driver_legend.axis('off')

    plt.suptitle(f'F1 {result_type} by Constructor and Driver')

    gs.tight_layout(fig, rect=(0,0,1,0.95))


def plot_wins_per_year(team_results, team_ids, team_names,
                       teams=['ferrari', 'mclaren', 'williams']):

    plt.figure(figsize=(10, 10))

    handles_team, labels_team = [], []
    # bin_counts = np.zeros((MAX_RACES_YEAR, 3))
    # bin_counts[:, 0] = np.arange(MAX_RACES_YEAR)
    for team in teams:
        team_ind = team_ids.index(team)

        first_win_ind = np.nonzero(team_results == team_ind)[0][0]
        years_participated = get_seasons_team(team) - 1950
        wins_per_year = np.sum(team_results[years_participated, :] == team_ind,
                               axis=1)

        # races_per_year = np.sum(team_results[years_participated, :] != 0, axis=1)
        # wins_per_year = wins_per_year / races_per_year

        winrate, nyears = np.unique(wins_per_year, return_counts=True)

        h1, = plt.plot(winrate, nyears, '-s',
                 ms=10, color=TEAM_COLORS[team][0])
        h2, = plt.plot(winrate, nyears, 'o',
                 ms=5, color=TEAM_COLORS[team][1])

        # for n_wins, n_years in zip(*np.unique(wins_per_year, return_counts=True)):
        #     bin_counts[n_wins, 1] = n_years

        # h1, = plt.plot(bin_counts[:, 0], bin_counts[:, 1], '-s',
        #          ms=10, color=TEAM_COLORS[team][0])
        # h2, = plt.plot(bin_counts[:, 0], bin_counts[:, 1], 'o',
        #          ms=5, color=TEAM_COLORS[team][1])

        handles_team.append((h1, h2))
        labels_team.append(f'{team_names[team]} ({len(years_participated)} years)')

        # bin_counts[:, 2] += bin_counts[:, 1]
#
    plt.legend(handles_team, labels_team)

    plt.xlabel('Number of Wins per Year')
    plt.ylabel('Number of Years')

    plt.title('Winning consistency of F1 teams')

    plt.savefig('f1_team_wins_per_year.png', dpi=200)
    plt.show()


def plot_num_unique_winners_per_year(team_results, team_ids, team_names):
    years = np.arange(F1_FIRST_YEAR, F1_LATEST_YEAR + 1)
    unique_winners_per_year = np.array([
        len(np.unique(team_results[year, team_results[year, :] != 0]))
        for year in range(len(team_results))
    ])

    plt.plot(years, unique_winners_per_year, '-', color='grey')
    plt.plot(years, unique_winners_per_year, 'o', color='k')

    plt.text(1982, 7.1, '1982\n7 unique teams', ha='center', va='bottom')
    plt.text(2012, 6.1, '2012\n6 unique teams', ha='center', va='bottom')

    plt.xlabel('Year')
    plt.ylabel('# Unique Team Winners')

    plt.ylim(1.75, 7.75)

    plt.title('Number of F1 Unique Winners across the years')

    plt.savefig('f1_unique_wins_per_year.png', dpi=200)
    plt.show()