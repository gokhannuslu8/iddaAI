import requests
import json

def check_endpoints():
    leagues = {
        "Premier League": 2021,
        "La Liga": 2014,
        "Bundesliga": 2002,
        "Serie A": 2019,
        "Ligue 1": 2015,
        "Eredivisie": 2003,
        "Primeira Liga": 2017,
        "Championship": 2016
    }
    
    headers = {"X-Auth-Token": "5eaabebe94b1429c8251bf127ad4adfa"}
    
    for league_name, league_id in leagues.items():
        print(f"\n{'='*50}")
        print(f"{league_name} (ID: {league_id})")
        print(f"{'='*50}")
        
        # 1. Lig bilgisi kontrolü
        try:
            comp_url = f"https://api.football-data.org/v4/competitions/{league_id}"
            comp_response = requests.get(comp_url, headers=headers)
            print(f"Lig bilgisi: {comp_response.status_code}")
            
            if comp_response.status_code == 200:
                comp_data = comp_response.json()
                print(f"  ✅ Lig mevcut: {comp_data.get('name')}")
                
                # 2. Takımlar endpoint'i kontrolü
                teams_url = f"https://api.football-data.org/v4/competitions/{league_id}/teams"
                teams_response = requests.get(teams_url, headers=headers)
                print(f"Takımlar endpoint: {teams_response.status_code}")
                
                if teams_response.status_code == 200:
                    teams_data = teams_response.json()
                    teams_count = len(teams_data.get('teams', []))
                    print(f"  ✅ Takımlar mevcut: {teams_count} takım")
                    
                    # 3. Maçlar endpoint'i kontrolü
                    matches_url = f"https://api.football-data.org/v4/competitions/{league_id}/matches"
                    matches_response = requests.get(matches_url, headers=headers)
                    print(f"Maçlar endpoint: {matches_response.status_code}")
                    
                    if matches_response.status_code == 200:
                        matches_data = matches_response.json()
                        matches_count = len(matches_data.get('matches', []))
                        print(f"  ✅ Maçlar mevcut: {matches_count} maç")
                    else:
                        print(f"  ❌ Maçlar endpoint kapalı: {matches_response.status_code}")
                        if matches_response.status_code == 403:
                            print("  📝 Ücretsiz planda bu endpoint kapalı")
                        elif matches_response.status_code == 404:
                            print("  📝 Bu sezon için maç verisi yok")
                else:
                    print(f"  ❌ Takımlar endpoint kapalı: {teams_response.status_code}")
            else:
                print(f"  ❌ Lig bulunamadı: {comp_response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Hata: {e}")
        
        # Rate limit için bekleme
        import time
        time.sleep(1)

if __name__ == "__main__":
    check_endpoints() 