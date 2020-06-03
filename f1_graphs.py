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
    'indy500': ('white', 'grey'),
    'others': ('black', 'black'),
}
MAX_RACES_YEAR = 21
F1_FIRST_YEAR = 1950
F1_LATEST_YEAR = 2020


def parse_dataframe(races_df_base, constructors_df):
    num_years = F1_LATEST_YEAR - F1_FIRST_YEAR + 1

    races_df = races_df_base.copy(deep=True)
    race_results = np.zeros((num_years, MAX_RACES_YEAR), dtype='u4')

    race_year_ind = races_df['year'] - F1_FIRST_YEAR
    race_round_ind = races_df['round'] - 1
    indy500_races = races_df['raceName'] == 'Indianapolis 500'

    races_df.loc[indy500_races, 'constructorId'] = constructors_df[
        constructors_df['constructorRef'] == 'indy500'
    ].index[0]
    race_results[race_year_ind, race_round_ind] = races_df['constructorId']

    return race_results


def parse_race_winners_team():
    races_df = get_all_race_winners()

    num_years = int(races_df[-1]['season']) - int(races_df[0]['season']) + 1

    team_ids = [None]
    team_names = {}
    race_results = np.zeros((num_years, MAX_RACES_YEAR), dtype='u4')

    for race in races_df:
        year_ind = int(race['season']) - int(races_df[0]['season'])
        race_ind = int(race['round']) - 1

        team_id = race['Results'][0]['Constructor']['constructorId']
        team_name = race['Results'][0]['Constructor']['name']

        # remove engine manufacturer
        # team_id = team_id.split('-')[0]
        # team_name = team_name.split('-')[0]

        # fix teams
        if team_id in ['team_lotus', 'lotus-climax', 'lotus-ford', 'lotus-brm']:
            team_id = 'lotus'
            team_name = 'Lotus'

        if 'brabham' in team_id:
            team_id = 'brabham'
            team_name = 'Brabham'

        if 'cooper' in team_id:
            team_id = 'cooper'
            team_name = 'Cooper'

        if 'mclaren' in team_id:
            team_id = 'mclaren'
            team_name = 'McLaren'

        if race['raceName'] == 'Indianapolis 500':
            team_id = 'indy500'
            team_name = 'Indianapolis 500'

        if team_id not in team_ids:
            team_ids.append(team_id)
            team_names[team_id] = team_name

        team_val = team_ids.index(team_id)

        race_results[year_ind, race_ind] = team_val
        # print(year_ind, race_ind, team_val, team_name)

    return race_results, team_ids, team_names


def plot_race_winners_team(race_results, constructors_df):
    fig = plt.figure(figsize=(6, 9.1))
    gs = GridSpec(1, 2, width_ratios=[1, 0.5], wspace=0)

    color_names_sq = np.array(
        ['white'] * (constructors_df.index.max() + 1), dtype='U16'
    )
    color_names_sq[constructors_df.index] = constructors_df['parent'].apply(
        lambda t: TEAM_COLORS.get(t, TEAM_COLORS['others'])[0]
    )
    # print(color_names_sq[131])

    cmap_sq = ListedColormap(color_names_sq)

    # Plot
    ax_left = plt.subplot(gs[0])
    ax_right = plt.subplot(gs[1])

    handles = []
    labels = []
    total_races = np.sum(race_results != 0)
    remaining_races = total_races

    xlims = (0.5, MAX_RACES_YEAR + 0.5)
    ylims = (F1_LATEST_YEAR + 0.5, F1_FIRST_YEAR - 0.5)

    ax_left.imshow(
        race_results, cmap=cmap_sq, vmin=0, vmax=constructors_df.index.max(),
        extent=(*xlims, *ylims)
    )

    team_ref_view = constructors_df.set_index('constructorRef')

    for team_id in TEAM_COLORS:
        if team_id == 'others':
            name = 'Others'
            race_wins = race_results != 0
            # for team_id in TEAM_COLORS:
            #     if team_id == 'others':
            #         continue

            team_ids = constructors_df[
                ~constructors_df['parent'].isin(TEAM_COLORS)
            ].index
        else:
            name = team_ref_view.loc[team_id]['name']
            team_ids = constructors_df[constructors_df['parent'] == team_id].index

        race_wins = np.isin(race_results, team_ids)

        wins = np.sum(race_wins)
        y, x = np.nonzero(race_wins)
        x += 1          # shift round #
        y += 1950       # shift year

        if wins == 0:
            continue

        colors = TEAM_COLORS[team_id]
        label = f'{name} ({wins} wins)'

        h1, = ax_left.plot(np.nan, 's', ms=7, color=colors[0])
        h2, = ax_left.plot(x, y, 'o', ms=3, color=colors[1])

        handles.append((h1, h2))
        labels.append(label)

    # ax_left.axis('off')
    ax_left.invert_yaxis()

    ax_left.set_xticks([1] + [i for i in range(5, 21, 5)])
    ax_left.set_yticks(
        [ i for i in range(F1_FIRST_YEAR, F1_LATEST_YEAR, 5)] + [F1_LATEST_YEAR]
    )

    ax_left.set_xlim(*xlims)
    ax_left.set_ylim(*ylims)

    ax_left.set_xlabel('Race #')
    ax_left.set_ylabel('Year')

    ax_right.legend(handles, labels, loc='center', facecolor=(.85, .85, .85))
    ax_right.axis('off')

    plt.suptitle('F1 Race Wins by Constructor')#, y=.95)

    gs.tight_layout(fig, rect=(0,0,1,0.95))


def plot_wins_per_year(race_results, team_ids, team_names,
                       teams=['ferrari', 'mclaren', 'williams']):

    plt.figure(figsize=(10, 10))

    handles, labels = [], []
    # bin_counts = np.zeros((MAX_RACES_YEAR, 3))
    # bin_counts[:, 0] = np.arange(MAX_RACES_YEAR)
    for team in teams:
        team_ind = team_ids.index(team)

        first_win_ind = np.nonzero(race_results == team_ind)[0][0]
        years_participated = get_seasons_team(team) - 1950
        wins_per_year = np.sum(race_results[years_participated, :] == team_ind,
                               axis=1)

        # races_per_year = np.sum(race_results[years_participated, :] != 0, axis=1)
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

        handles.append((h1, h2))
        labels.append(f'{team_names[team]} ({len(years_participated)} years)')

        # bin_counts[:, 2] += bin_counts[:, 1]
#
    plt.legend(handles, labels)

    plt.xlabel('Number of Wins per Year')
    plt.ylabel('Number of Years')

    plt.title('Winning consistency of F1 teams')

    plt.savefig('f1_team_wins_per_year.png', dpi=200)
    plt.show()


def plot_num_unique_winners_per_year(race_results, team_ids, team_names):
    years = np.arange(F1_FIRST_YEAR, F1_LATEST_YEAR + 1)
    unique_winners_per_year = np.array([
        len(np.unique(race_results[year, race_results[year, :] != 0]))
        for year in range(len(race_results))
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