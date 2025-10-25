import requests
import json

def get_current_teams():
    leagues = {
        "Premier League": 2021,
        "La Liga": 2014,
        "Bundesliga": 2002,
        "Serie A": 2019,
        "Ligue 1": 2015,
        "Eredivisie": 2003,
        "Primeira Liga": 2017
    }
    
    headers = {"X-Auth-Token": "5eaabebe94b1429c8251bf127ad4adfa"}
    
    for league_name, league_id in leagues.items():
        print(f"\n{'='*50}")
        print(f"{league_name} (ID: {league_id})")
        print(f"{'='*50}")
        
        try:
            url = f"https://api.football-data.org/v4/competitions/{league_id}/teams"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                teams_data = response.json()
                teams = teams_data.get('teams', [])
                print(f"Takım sayısı: {len(teams)}")
                
                team_names = []
                for team in teams:
                    name = team.get('name', '')
                    # Kısa isimleri al
                    short_name = team.get('shortName', name)
                    team_names.append(short_name)
                    print(f"  - {short_name} (ID: {team.get('id')})")
                
                # Python listesi formatında yazdır
                print(f"\nPython listesi:")
                print(f'"{league_name}": [')
                for i, name in enumerate(team_names):
                    if i == len(team_names) - 1:
                        print(f'    "{name}"')
                    else:
                        print(f'    "{name}",')
                print("],")
                
            else:
                print(f"API hatası: {response.status_code}")
                
        except Exception as e:
            print(f"Hata: {e}")
        
        # Rate limit için bekleme
        import time
        time.sleep(2)

if __name__ == "__main__":
    get_current_teams() 