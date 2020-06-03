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


def plot_results_year_round_team_color(race_results, constructors_df,
                                       result_type='Race Wins'):
    fig = plt.figure(figsize=(6, 9.1))
    gs = GridSpec(1, 3, width_ratios=[1, 0.3, 0.5], wspace=0)

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
    ax_champs = plt.subplot(gs[1])
    ax_legend = plt.subplot(gs[2])

    handles = []
    labels = []
    total_races = np.sum(race_results != 0)
    remaining_races = total_races

    xlims = (0.5, MAX_RACES_YEAR + 0.5)
    ylims = (F1_LATEST_YEAR + 0.5, F1_FIRST_YEAR - 0.5)

    ax_results.imshow(
        race_results, cmap=cmap_sq, vmin=0, vmax=constructors_df.index.max(),
        extent=(*xlims, *ylims)
    )

    team_ref_view = constructors_df.set_index('constructorRef')

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

        race_wins = np.isin(race_results, team_ids)

        wins = np.sum(race_wins)
        y, x = np.nonzero(race_wins)
        x += 1          # shift round #
        y += 1950       # shift year

        if wins == 0:
            continue

        colors = TEAM_COLORS[team_id]
        if wins == 1:
            wins_label = f'{wins} race'
        else:
            wins_label = f'{wins} races'
        label = f'{name} ({wins_label})'

        team_n_races.append((n, team_id, wins))

        h1, = ax_results.plot(np.nan, 's', ms=7, color=colors[0])
        h2, = ax_results.plot(x, y, 'o', ms=3, color=colors[1])

        handles.append((h1, h2))
        labels.append(label)

    team_n_races = np.array(team_n_races, dtype=('u4,U16,u4'))
    order = np.hstack((
        np.argsort(team_n_races[
            ~np.isin(team_n_races['f1'], ['indy500', 'others'])
        ]['f2'])[::-1],
        np.nonzero(team_n_races['f1'] == 'indy500')[0],
        np.nonzero(team_n_races['f1'] == 'others')[0]
    ))

    # ax_results.axis('off')
    ax_results.invert_yaxis()

    ax_results.set_xticks([1] + [i for i in range(5, 21, 5)])
    ax_results.set_yticks(
        [ i for i in range(F1_FIRST_YEAR, F1_LATEST_YEAR, 5)] + [F1_LATEST_YEAR]
    )

    ax_results.set_xlim(*xlims)
    ax_results.set_ylim(*ylims)

    ax_results.set_xlabel('Race #')
    ax_results.set_ylabel('Year')

    handles = [handles[n] for n in order]
    labels = [labels[n] for n in order]

    ax_legend.legend(handles, labels, loc='center', facecolor=(.85, .85, .85))
    ax_legend.axis('off')

    plt.suptitle(f'F1 {result_type} by Constructor')

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