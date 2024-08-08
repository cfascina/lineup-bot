import configparser
import json
import requests

config = configparser.ConfigParser()
config.read('config.ini')

def get_current_round():
    url = config['APIS']['status']
    req = requests.get(url)

    return req.json()['rodada_atual']

def get_data():
	req = requests.get(config['APIS']['lineups'])
	
	return req.json()

def get_lineup(data, team_type, round_id):
	lineup = {}
	
	for player in data[team_type][round_id]:
		lineup[int(player['player_id'])] = {
			"name": player['player_name'],
			"position": player['position'],
			"position_id": player['position_id'],
			"club": player['club_name'],
			"starting": True if player['titular'] == 1 else False,
			"captain": True if player['captain'] == 1 else False
	}
	
	return lineup

def set_payload(scheme_id, lineup):
    payload = {
        "esquema": scheme_id,
        "atletas": [],
        "capitao": None,
        "reservas": {}
    }

    for player_id, data in lineup.items():    
        payload["atletas"].append(player_id) if data['starting'] else None
        payload["capitao"] = player_id if data['captain'] and payload.get("capitao") is None else payload.get("capitao")

        if not data['starting']:
            payload["reservas"][str(data['position_id'])] = player_id

    return payload

def set_lineup(team_type, payload):
	token = config['TEAM_KEYS']['valuation'] if team_type == 'time_valorizacao' else config['TEAM_KEYS']['scoring']
	params = {
		'Content-Type': 'application/json',
		'Authorization': f"Bearer {token}"
	}

	try:
		print(f"Escalando time {team_type}...")
		post = requests.post(url = config['APIS']['save'], json = payload, headers = params)
	except Exception as e:
		print(e)

	return post

def show_team(team_type, scheme_id, lineup):
    schemes = {1: "3-4-3", 2: "3-5-2", 3: "4-3-3", 4: "4-4-2", 5: "4-5-1", 6: "5-3-2", 7: "5-4-1"}
    print(f"{team_type.replace('_', ' ').upper()} ({schemes.get(scheme_id)})")

    positions = ['TEC', 'GOL', 'LAT', 'ZAG', 'MEI', 'ATA']
    players = []
    substitutes = []

    for player, data in lineup.items():
        if data['starting']:
            players.append([
                data['position'],
                True if data['captain'] else False,
                data['name'],
                data['club']
        ])
        else:
            substitutes.append([
                data['position'],
                False,
                data['name'],
                data['club']
        ])

    players = sorted(players, key = lambda x: positions.index(x[0]))
    substitutes = sorted(substitutes, key = lambda x: positions.index(x[0]))
    players.extend(substitutes)

    for i, player in enumerate(players):
        print('\nTITULARES') if i == 0 else None
        print('\nRESERVAS') if i == 12 else None
        print(f"({player[0]}) {'[C]' if player[1] else '[ ]'} {player[2]} - {player[3]}")
    
    print('-' * 50)


current_round = get_current_round()
data = get_data()

for team_type in ['time_valorizacao', 'selecao_do_guru']:
	rounds = data[team_type].keys()
	round_id = str(max(list(map(int, rounds))))
	scheme_id = data[team_type][round_id][0]['esquema_id']
	lineup = get_lineup(data, team_type, round_id)
	payload = set_payload(scheme_id, lineup)	
	post = set_lineup(team_type, payload)

	if post.ok:
		print(f"Time escalado com sucesso.") 
		show_team(team_type, scheme_id, lineup)
	else:
		response = json.loads(post.content.decode('utf-8'))
		print(f"Falha ao escalar time: {post.status_code} / {response['mensagem']}")
