import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.gridspec import GridSpec
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from f1_api import get_all_race_winners, get_seasons_team


TEAM_COLORS = {
    'ferrari': ('red', 'red'),
    'mclaren': ('orange', 'orange'),
    'williams': ('blue', 'blue'),
    'mercedes': ('aqua', 'aqua'),
    'lotus': ('black', 'gold'),
    'red_bull': ('indigo', 'indigo'),
    'brabham': ('mediumseagreen', 'black'),
    # 'renault': ('black', 'orange'),
    'renault': ('deepskyblue', 'yellow'),
    'alpine': ('royalblue', 'pink'),
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
    'alphatauri': ('white', 'black'),
    'bmw_sauber': ('white', 'blue'),
    'stewart': ('white', 'green'),
    'porsche': ('bisque', 'gold'),
    'eagle': ('blue', 'red'),
    'hesketh': ('brown', 'blue'),
    'penske': ('pink', 'cyan'),
    'shadow': ('darkgrey', 'brown'),
    'force_india': ('pink', 'pink'),
    'racing_point': ('pink', 'black'),
    'aston_martin': ('lightseagreen', 'yellow'),
    'toyota': ('lightgrey', 'red'),
    'sauber': ('firebrick', 'white'),
    'bar': ('darkgoldenrod', 'red'),
    'haas': ('darkgoldenrod', 'black'),
    'rb': ('darkblue', 'white'),
    'indy500': ('lightgrey', 'white'),
    'others': ('dimgrey',)*2,
    'emptyOrange': ('dimgrey',)*2,
    'emptyBrown': ('dimgrey',)*2,
    # 'emptyOrange': ('peru',)*2,
    # 'emptyBrown': ('brown',)*2,
}
DRIVER_COLORS = {
    'fangio': ('black', 'h'),
    'moss': ('white', 's'),
    'jack_brabham': ('yellow', '>'),
    'clark': ('cyan', 's'),
    'stewart': ('red', '^'),
    'lauda': ('blue', 's'),
    'piquet': ('yellow', 'o'),
    'prost': ('white', '^'),
    'senna': ('cyan', 'v'),
    'mansell': ('black', 's'),
    'damon_hill': ('cyan', 'o'),
    'hakkinen': ('black', 'v'),
    'michael_schumacher': ('white', '*'),
    'alonso': ('white', 'v'),
    'raikkonen': ('lawngreen', '<'),
    'vettel': ('yellow', 's'),
    'hamilton': ('black', '*'),
    'max_verstappen': ('orange', '^'),
}
MAX_RACES_YEAR = 25
F1_FIRST_YEAR = 1950
F1_LATEST_YEAR = 2024
DEFAULT_FIG_SIZE = (9, 9)


def got_most_wins(group, champions_df):
    counts = group.value_counts()       # returns table of Id - #wins
    rows_with_max_wins = counts[counts == counts.max()].index

    if len(rows_with_max_wins) == 1:
        row_most_wins = rows_with_max_wins[0]
    else:
        year = group.name
        is_champ = rows_with_max_wins.isin(champions_df.loc[year])
        if is_champ.any():
            row_most_wins = rows_with_max_wins[is_champ][0]
        else:
            row_most_wins = rows_with_max_wins[0]

    return row_most_wins


def parse_dataframe(races_df_base, constructors_df, champions_df,
                    show_championships=False):
    num_years = F1_LATEST_YEAR - F1_FIRST_YEAR + 1

    races_df = races_df_base.copy(deep=True)
    team_results = np.zeros((num_years, MAX_RACES_YEAR), dtype='u4')
    driver_results = np.zeros((num_years, MAX_RACES_YEAR), dtype='u4')

    if 'points' in races_df.columns:
        # Some races had cars with multiple drivers - drop the one with the least points
        races_view = races_df.reset_index().set_index(['raceId', 'points'])
        has_mult_drivers = races_df.index.duplicated(False)     # select all duplicate rows
        min_points = races_df[has_mult_drivers] \
            .groupby('raceId') \
            .min('points')['points'] \
            .reset_index()                                      # DF with raceId, points to drop
        races_view.drop(index=pd.MultiIndex.from_frame(min_points), inplace=True)
        races_df = races_view.reset_index().set_index('raceId')

    # Fix Indy 500 winners
    indy500_races = races_df['raceName'] == 'Indianapolis 500'
    races_df.loc[indy500_races, 'constructorId'] = constructors_df[
        constructors_df['constructorRef'] == 'indy500'
    ].index[0]

    # Add results to numpy tables
    race_year_ind = races_df['year'] - F1_FIRST_YEAR
    race_round_ind = races_df['round'] - 1
    team_results[race_year_ind, race_round_ind] = races_df['constructorId']
    driver_results[race_year_ind, race_round_ind] = races_df['driverId']

    if show_championships:
        # Get teams/drivers with most wins in a year
        races_years = races_df.groupby('year')
        # got_most_wins = lambda r: r.value_counts().index[0]

        team_most_wins = races_years['constructorId'].apply(
            got_most_wins, champions_df['wcc']
        )
        driver_most_wins = races_years['driverId'].apply(got_most_wins, champions_df['wdc'])

        team_most_wins = team_most_wins.to_numpy().reshape((-1, 1))
        driver_most_wins = driver_most_wins.to_numpy().reshape((-1, 1))

        # Fix WCC only starting in 1958 or still not decided
        for year in range(F1_FIRST_YEAR, F1_LATEST_YEAR + 1):
            if year in champions_df['wcc'].index:
                continue

            champions_df['wcc'].loc[year] = 0

        champions_df['wcc'].sort_index(inplace=True)

        # Fix WDC still not decided
        for year in range(F1_FIRST_YEAR, F1_LATEST_YEAR + 1):
            if year in champions_df['wdc'].index:
                continue

            champions_df['wdc'].loc[year] = 0

        champions_df['wdc'].sort_index(inplace=True)

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
                                       result_type='Race Wins',
                                       show_teams=True,
                                       show_drivers=False,
                                       min_team_wins=20):

    if not show_drivers and not show_teams:
        return

    fig = plt.figure(figsize=DEFAULT_FIG_SIZE)
    gs = GridSpec(1, 3, width_ratios=[1, 0.7, 0.5], wspace=0)
    # if show_drivers and show_teams:
    # else:
    #     gs = GridSpec(1, 3, width_ratios=[1.3, 0.4, 0.4], wspace=0.1)

    team_results = results['team']
    # hide driver championships from results
    if not show_drivers and team_results.shape[1] > MAX_RACES_YEAR:
        team_results = team_results[:, :-3]

    driver_results = results['driver']
    # hide team championships from results
    if not show_teams and driver_results.shape[1] > MAX_RACES_YEAR:
        team_results = np.delete(team_results, [-6, -5, -4], axis=1)
        driver_results = np.delete(driver_results, [-6, -5, -4], axis=1)

    team_ref_view = constructors_df.set_index('constructorRef')
    driver_ref_view = drivers_df.set_index('driverRef')

    # remove teams (either teams are hidden, or do not have enough wins)
    team_race_wins = {}
    team_final_colors = dict(TEAM_COLORS)
    for n, team_id in enumerate(TEAM_COLORS):
        if team_id == 'others':
            name = 'Others'
            team_ids = constructors_df[
                ~constructors_df['parent'].isin(team_final_colors)
            ].index
        else:
            name = team_ref_view.loc[team_id]['name']
            team_ids = constructors_df[constructors_df['parent'] == team_id].index

        race_wins = np.isin(team_results, team_ids)
        team_race_wins[team_id] = (name, race_wins)

        wins = np.sum(race_wins[:, :MAX_RACES_YEAR])

        remove_team_color = (
            (
                not show_teams and
                team_id != 'others' and
                not team_id.startswith('empty')
            )
            or
            (
                (wins < min_team_wins) and (
                    team_id not in ['indy500', 'others'] and
                    not team_id.startswith('empty')
                )
            )
        )

        if remove_team_color:
            team_final_colors.pop(team_id)
            continue

    color_names_sq = np.array(
        ['lightgrey'] * (constructors_df.index.max() + 1), dtype='U16'
    )
    color_names_sq[constructors_df.index] = constructors_df['parent'].apply(
        lambda t: team_final_colors.get(t, team_final_colors['others'])[0]
    )

    cmap_sq = ListedColormap(color_names_sq)

    # Plot
    ax_results = plt.subplot(gs[0])

    if show_teams:
        ax_team_legend = plt.subplot(gs[1])

    if show_drivers:
        ax_driver_legend = plt.subplot(gs[2])

    xlims = (0.5, team_results.shape[1] + 0.5)
    ylims = (F1_LATEST_YEAR + 0.5, F1_FIRST_YEAR - 0.5)

    # Races
    handles_team = []
    labels_team = []
    handles_driver = []
    labels_driver = []

    ax_results.imshow(
        team_results, cmap=cmap_sq, vmin=0, vmax=constructors_df.index.max(),
        extent=(*xlims, *ylims)
    )

    team_n_races = []
    for n, team_id in enumerate(team_final_colors):
        name, race_wins = team_race_wins[team_id]

        wins = np.sum(race_wins[:, :MAX_RACES_YEAR])
        y, x = np.nonzero(race_wins)
        x += 1          # shift round #
        y += 1950       # shift year

        if wins == 0:
            continue

        colors = team_final_colors[team_id]
        if wins == 1:
            wins_label = f'{wins} {win_type}'
        else:
            wins_label = f'{wins} {win_type}s'
        label = f'{name} ({wins_label})'

        team_n_races.append((n, team_id, wins))

        h1, = ax_results.plot(np.nan, 's', ms=7, color=colors[0])
        h2, = ax_results.plot(x, y, 'o', ms=1.5, color=colors[1])

        handles_team.append((h1, h2))
        labels_team.append(label)

    if show_drivers:
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

            color, symbol = DRIVER_COLORS[driver_ref]
            if wins == 1:
                wins_label = f'{wins} {win_type}'
            else:
                wins_label = f'{wins} {win_type}s'

            first_year = min(y)
            last_year = max(y)

            label = f'{name}\n{first_year}-{last_year} ({wins_label})'

            driver_n_races.append((n, driver_ref, wins))

            h, = ax_results.plot(x, y, symbol, ms=6, color=color,
                                markeredgewidth=1,
                                markerfacecolor='none')

            handles_driver.append(h)
            labels_driver.append(label)

    team_n_races = np.array(team_n_races, dtype=('u4,U16,u4'))      # fields (f0, f1, f2) = (n, team_id, wins)
    order_team = np.hstack((
        np.argsort(team_n_races[
            ~np.isin(team_n_races['f1'], ['indy500', 'others'])
        ]['f2'])[::-1],
        np.nonzero(team_n_races['f1'] == 'indy500')[0],
        np.nonzero(team_n_races['f1'] == 'others')[0],
    ))

    if show_drivers:
        driver_n_races = np.array(driver_n_races, dtype=('u4,U16,u4'))
        order_driver = np.argsort(driver_n_races['f2'])[::-1]

    # ax_results.axis('off')
    ax_results.invert_yaxis()

    # ax_results.invert_yaxis()

    ax_results.set_xticks([1] + [i for i in range(5, 21, 5)])
    ax_results.set_yticks(
        [ i for i in range(F1_FIRST_YEAR, F1_LATEST_YEAR, 5)] #+ [F1_LATEST_YEAR]
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

    def add_line_label(x, y, label, ha='center', va='top', color='black',
                       mult=1):
        signal = 1 if va == 'top' else -1

        line = mlines.Line2D(
            [x, x],
            [y + 1 * signal, y + 2 * signal * mult],
            ls='-', color=color
        )
        line.set_clip_on(False)
        ax_results.add_line(line)

        ax_results.text(x, y + 2 * signal * mult, label,
                        ha=ha, va=va, color=color)

    if team_results.shape[1] > MAX_RACES_YEAR:
        col0 = MAX_RACES_YEAR + 1
        col1 = col0 + 3 * show_teams

        if show_teams:
            add_line_label(col0 + 2, F1_LATEST_YEAR, 'WCC  ',
                        ha='center', va='top', color='blue')
            add_line_label(col0 + 3, F1_FIRST_YEAR, 'Constructor\nwith most wins',
                        ha='right', va='bottom', color='blue')

        if show_drivers:
            add_line_label(col1 + 2, F1_LATEST_YEAR, '  WDC',
                        ha='center', va='top', color='brown')
            add_line_label(col1 + 3, F1_FIRST_YEAR, 'Driver with\nmost wins',
                        ha='right', va='bottom', color='brown',
                        mult=3)

    # Team legend
    if show_teams:
        handles_team = [handles_team[n] for n in order_team]
        labels_team = [labels_team[n] for n in order_team]

        ax_team_legend.legend(handles_team, labels_team, loc='center',
                            facecolor='lightgrey')
        ax_team_legend.axis('off')

    # Driver legend
    if show_drivers:
        # handles_driver = [handles_driver[n] for n in order_driver]
        # labels_driver = [labels_driver[n] for n in order_driver]

        ax_driver_legend.legend(handles_driver, labels_driver, loc='center',
                                facecolor='lightgrey')
        ax_driver_legend.axis('off')

    title = f'F1 {result_type}'
    if show_teams:
        title += ' by Constructor'
    if min_team_wins > 0:
        title += f' (with at least {min_team_wins} wins)'
    if show_drivers:
        title += ' and Driver'
    plt.suptitle(title)

    gs.tight_layout(fig, rect=(0,0,1,0.95), pad=0)


def plot_wins_per_year(team_results, constructors_df,
                       teams=['ferrari', 'mclaren', 'williams', 'mercedes', 'red_bull']):

    team_ref_view = constructors_df.set_index('constructorRef')

    n_total = len(teams)
    bar_width = 1 / (n_total + 2)

    plt.figure(figsize=(10, 10))

    handles_team, labels_team = [], []
    # bin_counts = np.zeros((MAX_RACES_YEAR, 3))
    # bin_counts[:, 0] = np.arange(MAX_RACES_YEAR)
    for n, team in enumerate(teams):
        team_ind = constructors_df[constructors_df['constructorRef'] == team].index[0]

        first_win_ind = np.nonzero(team_results == team_ind)[0][0]
        years_participated = get_seasons_team(team) - F1_FIRST_YEAR
        wins_per_year = np.sum(team_results[years_participated, :] == team_ind,
                               axis=1)

        # races_per_year = np.sum(team_results[years_participated, :] != 0, axis=1)
        # wins_per_year = wins_per_year / races_per_year

        winrate, nyears = np.unique(wins_per_year, return_counts=True)

        color_bg = TEAM_COLORS[team][0]
        color_fg = TEAM_COLORS[team][1]

        x_pos = winrate + (n - n_total/2)*bar_width

        # plt.bar(
        #     x_pos, nyears, width=bar_width, color=color_bg, edgecolor=color_fg, hatch='o'
        # )
        # plt.bar(
        #     x_pos, nyears, width=bar_width, color='none', edgecolor=color_bg
        # )

        h1, = plt.plot(winrate, nyears, '-s', ms=10, color=TEAM_COLORS[team][0])
        h2, = plt.plot(winrate, nyears, 'o', ms=5, color=TEAM_COLORS[team][1])

        # for n_wins, n_years in zip(*np.unique(wins_per_year, return_counts=True)):
        #     bin_counts[n_wins, 1] = n_years

        # h1, = plt.plot(bin_counts[:, 0], bin_counts[:, 1], '-s',
        #          ms=10, color=TEAM_COLORS[team][0])
        # h2, = plt.plot(bin_counts[:, 0], bin_counts[:, 1], 'o',
        #          ms=5, color=TEAM_COLORS[team][1])

        handles_team.append((h1, h2))
        labels_team.append(f'{team_ref_view.loc[team]["name"]} ({len(years_participated)} years)')

        # bin_counts[:, 2] += bin_counts[:, 1]
#
    plt.legend(handles_team, labels_team)

    plt.xlabel('Number of Wins per Year')
    plt.ylabel('Number of Years')

    plt.title('Winning consistency of F1 teams')

    plt.savefig('images/f1_team_wins_per_year.png', dpi=200)
    plt.show()


def plot_num_unique_winners_per_year(team_results):
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

    plt.savefig('images/f1_unique_wins_per_year.png', dpi=200)
    plt.show()


def plot_team_colors(constructors_df):
    plt.figure(figsize=(DEFAULT_FIG_SIZE[0], 10))
    plt.axis('off')

    team_ref_view = constructors_df.set_index('constructorRef')

    num_colors = len(TEAM_COLORS)

    table_text = []
    no_colors = [
        team for team in constructors_df['constructorRef']
        if team.split('-')[0] not in TEAM_COLORS
    ]

    for n, team_id in enumerate(TEAM_COLORS):
        if team_id == 'others':
            team_name = 'Others'
        else:
            team_name = team_ref_view.loc[team_id]['name']

        colors = TEAM_COLORS[team_id]

        table_text.append((
            team_id, team_name, *colors
        ))

        x, y = 0.05, num_colors - n - 0.5

        plt.plot(x, y, 's', color=colors[0], ms=7)
        plt.plot(x, y, 'o', color=colors[1], ms=3)

    tbl = plt.table(
        table_text,
        colLabels=('ID', 'Name', 'BG Colour', 'FG Colour'),
        colWidths=(.3, .3, .2, .2),
        # bbox=(0.05, 0., .95, 1.0),
        bbox=(0, 0, 1, 1),
        # edges='horizontal',
        edges='B',
        loc='center',
    )

    # tbl.auto_set_font_size(False)
    # tbl.set_fontsize(8)

    plt.xlim(0, 1)
    plt.ylim(0, num_colors + 1)

    plt.tight_layout()

    return no_colors

def plot_driver_and_team_colors(races_race_winners, constructors_df):
    n_drivers = len(DRIVER_COLORS)
    n_races = 6

    team_info = constructors_df.reset_index().set_index('constructorRef')

    plt.figure(figsize=(n_races, n_drivers))

    bg_array = np.zeros((n_drivers, n_races), dtype='u4')
    bg_colors = dict()
    driver_colors = []
    for y, driver_name in enumerate(DRIVER_COLORS):
        color, symbol = DRIVER_COLORS[driver_name]

        teams = races_race_winners[
            races_race_winners['driverRef'] == driver_name
        ]['constructorRef']
        teams = [
            'lotus' if t_ref == 'team_lotus' else
            team_info.loc[t_ref]['parent']
            for t_ref in teams
        ]
        teams = np.unique(teams)

        team_colors = []
        for x, team_ref in enumerate(teams):
            team_id = team_info.loc[team_ref]['constructorId']

            color_bg, color_fg = TEAM_COLORS[team_ref]

            bg_array[y, x] = team_id
            bg_colors[team_id] = color_bg
            team_colors.append((color_fg, color, symbol))

        driver_colors.append(team_colors)

    color_names_sq = np.array(['lightgrey'] * (bg_array.max() + 1), dtype='U16')
    for t_id in bg_colors:
        color_names_sq[t_id] = bg_colors[t_id]
    cmap_sq = ListedColormap(color_names_sq)

    xlims = (-0.5, n_races - 0.5)
    ylims = (n_drivers - 0.5, -0.5)

    plt.imshow(
        bg_array, cmap=cmap_sq, vmin=0, vmax=bg_array.max(),
        extent=(*xlims, *ylims)
    )

    for y, driver_color in enumerate(driver_colors):
        for x, (color_fg, color, symbol) in enumerate(driver_color):
            plt.plot(x, y, 'o', ms=20, color=color_fg)
            plt.plot(x, y, symbol, ms=60, color=color,
                    markeredgewidth=7,
                    markerfacecolor='none')

    plt.xticks([])#np.arange(n_races))
    plt.yticks([])#np.arange(n_drivers), DRIVER_COLORS.keys())

    plt.tight_layout()
