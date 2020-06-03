import requests
import json
import numpy as np

# website: https://ergast.com/mrd/

def get_all_race_winners():
    races = []
    limit = 100
    offset = 0

    while True:
        raw_response = requests.get(
            'http://ergast.com/api/f1/results/1.json'
            f'?limit={limit}&offset={offset}'
        )

        if raw_response.status_code != 200:
            raise Warning(f'status code {raw_response.status_code}')

        json_data = json.loads(raw_response.text)

        total_races = int(json_data['MRData']['total'])

        races += json_data['MRData']['RaceTable']['Races']

        if (offset + limit) > total_races:
            break

        offset += limit

    with open('race_winners.json', 'w') as f:
        json.dump(races, f, indent=2)

    return races


def get_all_race_results():
    races = []
    limit = 100
    offset = 0

    while True:
        raw_response = requests.get(
            'http://ergast.com/api/f1/results.json'
            f'?limit={limit}&offset={offset}'
        )

        if raw_response.status_code != 200:
            raise Warning(f'status code {raw_response.status_code}')

        json_data = json.loads(raw_response.text)

        total_races = int(json_data['MRData']['total'])

        races += json_data['MRData']['RaceTable']['Races']

        if (offset + limit) > total_races:
            break

        offset += limit

    with open('race_results.json', 'w') as f:
        json.dump(races, f, indent=2)

    return races


def get_seasons_team(team_id='ferrari'):
    raw_response = requests.get(
        f'http://ergast.com/api/f1/constructors/{team_id}/seasons.json?limit=100'
    )

    if raw_response.status_code != 200:
        raise Warning(f'status code {raw_response.status_code}')

    data = json.loads(raw_response.text)

    seasons = data['MRData']['SeasonTable']['Seasons']
    years = [int(s['season']) for s in seasons]

    return np.array(years)
