from os import name
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

plt.style.use('default')

DATES_RELEVANT = {
    'Aus GP 2013': '2013-03-19',
    'Aus GP 2014': '2014-03-14',
    'Aus GP 2015': '2015-03-15',
    'Aus GP 2016': '2016-03-20',
    'Aus GP 2017': '2017-03-26',
    'Aus GP 2018': '2018-03-25',
    'Aus GP 2019': '2019-03-17',
    'RBR GP 2020': '2020-07-05',
    'Bah GP 2021': '2021-03-30',
    'DTS S1': '2019-03-08',
    'DTS S2': '2020-02-28',
    'DTS S3': '2021-03-19',
    ('Alonso Indy Test', 'brown'): '2017-05-20',
    ('2019 German GP', 'orange'): '2019-07-28',
    ('Phoenix Grosjean', 'red'): '2020-11-29',
    # ('Kimi', 'green'): '2018-10-21',
}


def array_reshaped_to_n_columns(data, n_point):
    return np.reshape(
        data[:data.size - (data.size % n_point)],
        (-1, n_point)
    )


def n_point_average(data, n_point):
    if n_point == 1:
        return data

    return np.median(
        array_reshaped_to_n_columns(data, n_point),
        axis=1
    )


def smooth_data(raw_data, n_avg_points=5):
    dates_derv_smooth = array_reshaped_to_n_columns(
        raw_data['date'][:-1], n_avg_points
    )[:, n_avg_points//2]
    subs_derv_smooth = np.mean(array_reshaped_to_n_columns(
        np.diff(raw_data['subs']), n_avg_points
    ), axis=1)

    return dates_derv_smooth, subs_derv_smooth


def plot_times(max_val=30000):
    for name in DATES_RELEVANT:
        date = np.datetime64(DATES_RELEVANT[name])

        if isinstance(name, tuple):
            name, color = name
            plt.text(date, max_val+100, name,
                     color=color,
                     ha='center', va='bottom')
        elif 'GP' in name:
            color = 'cyan'
        elif 'DTS' in name:
            color = 'blue'
        else:
            color = 'k'

        plt.axvline(date, color=color, ls='-')

    plt.plot(np.nan, '-', color='cyan', label='First GP of the year')
    plt.plot(np.nan, '-', color='blue', label='Release of new season of DTS')


def plot_subs_in_time(dataframe):
    min_val = float(dataframe.min()) * 1.1
    max_val = float(dataframe.max()) * 1.1

    plt.figure(figsize=(10, 6))

    plot_times(max_val)

    plt.plot(dataframe)

    plt.xlabel('Date')
    plt.ylabel('Subs')

    plt.xlim('2013', '2021-06')
    plt.ylim(min_val, max_val)

    plt.legend()

    plt.title('Subs of r/formula1 over time', y=1.05)

    plt.tight_layout()
    plt.savefig('images/reddit_subs.jpg', dpi=150)

    plt.show()


def plot_derv_subs_in_time(dataframe):
    smooth_df = dataframe.resample('1W-WED').mean().diff()

    min_val = float(smooth_df.min()) * 1.1
    max_val = float(smooth_df.max()) * 1.1

    plt.figure(figsize=(10, 6))

    plt.axhline(0, color='k')
    plot_times(max_val)

    # plt.plot(df.diff(), '.', color='gray', ms=2,
    #          label='Sub Gain')
    plt.plot(smooth_df, 'k-', lw=2,
             label='Sub Gain (smoothed)')

    plt.xlabel('Date')
    plt.ylabel('Subs / Week')

    plt.xlim('2013', '2021-06')
    plt.ylim(min_val, max_val)

    plt.legend()

    plt.title('Growth of r/formula1 over time', y=1.05)

    plt.tight_layout()
    plt.savefig('images/reddit_subs_gain_week.jpg', dpi=150)

    plt.show()


# data = np.genfromtxt('data/r_formula1_subscribers.csv',
#                      dtype='datetime64[D],i4',
#                      names=True,
#                      delimiter=',')

df = pd.read_csv('data/r_formula1_subscribers.csv',
                 index_col=0, header=0, parse_dates=True)

# Subs in time
plot_subs_in_time(df)

# Sub gain in time
plot_derv_subs_in_time(df)


