# %%
import configparser
import pandas as pd
import requests

# %%
config = configparser.ConfigParser()
config.read('config.ini')

# %%
def get_status():
	url = f"{config['APIS']['status']}"
	req = requests.get(url)
	status = req.json()['status_mercado']
	current_round = req.json()['rodada_atual']
	
	return status, current_round

# %%
def get_round_data(team_id, round_id):
	url = f"{config['APIS']['team']}/{team_id}/{round_id}"
	req = requests.get(url)
	team_name = req.json()['time']['nome']
	points = req.json()['pontos']
	
	return team_name, points

# %%
def get_results(teams, current_round, status):
	results = {}

	for team_id in teams:
		results[team_id] = {}
		
		for round_id in range(20, 39):
			if round_id < current_round:
				if round_id == current_round and status != 1:
					pass
				else:
					team_name, points = get_round_data(team_id, round_id)
					
					if 'name' not in results[team_id]:
						results[team_id]['name'] = team_name
						results[team_id]['points'] = {}
					
					results[team_id]['points'][round_id] = points

	return results

# %%
def set_dataframe(results):
	rows = []

	for key, value in results.items():
		name = value['name']
		for round_number, points in value['points'].items():
			rows.append({'name': name, 'round': round_number, 'points': points})
			
	df = pd.DataFrame(rows)
	df_pivoted = df.pivot(index = 'name', columns = 'round', values = 'points')
	df_pivoted.columns = [f"#{col}" for col in df_pivoted.columns]
	df_pivoted.reset_index(inplace = True)

	return df_pivoted

# %%
def organize_dataframe(df):
	cols_rounds = df.select_dtypes(include = 'number').columns.tolist()
	df['total'] = df[cols_rounds].sum(axis = 1)

	df_cols = df.columns.tolist()
	df_cols.insert(df_cols.index('name') + 1, df_cols.pop(df_cols.index('total')))
	df = df[df_cols]

	df = df.sort_values(by='total', ascending = False).reset_index(drop = True)
	df.index += 1

	return df

# %%
status, current_round = get_status()

# %%
teams = ['204740', '2233005', '1185983', '8168228', '14565087', '13915560', '13952016', '18120927', '19558186', '47811882', '48532230']

# %%
results = get_results(teams, current_round, status)

# %%
df = set_dataframe(results)

# %%
df = organize_dataframe(df)

print(df)

