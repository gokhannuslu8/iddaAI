TEAM_ID_MAPPING = {
    # Premier League
    "AFC Bournemouth": 1044,
    "Arsenal": 57,
    "Aston Villa": 58,
    "Brentford": 402,
    "Brighton": 397,
    "Chelsea": 61,
    "Crystal Palace": 354,
    "Everton": 62,
    "Fulham": 63,
    "Ipswich": 349,
    "Leicester": 338,
    "Liverpool": 64,
    "Manchester City": 65,
    "Manchester United": 66,
    "Newcastle": 67,
    "Nottingham Forest": 351,
    "Southampton": 340,
    "Tottenham": 73,
    "West Ham": 563,
    "Wolves": 76,

    # La Liga
    "Athletic Bilbao": 77,
    "Osasuna": 79,
    "Leganes": 745,
    "Atletico Madrid": 78,
    "Alaves": 263,
    "Barcelona": 81,
    "Getafe": 82,
    "Girona": 298,
    "Celta Vigo": 558,
    "Espanyol": 80,
    "Mallorca": 89,
    "Rayo Vallecano": 87,
    "Real Betis": 90,
    "Real Madrid": 86,
    "Real Sociedad": 92,
    "Real Valladolid": 250,
    "Sevilla": 559,
    "Las Palmas": 275,
    "Valencia": 95,
    "Villarreal": 94,

    # Bundesliga
    "Heidenheim": 44,
    "Union Berlin": 28,
    "Mainz": 15,
    "Leverkusen": 3,
    "Dortmund": 4,
    "Mönchengladbach": 18,
    "Eintracht Frankfurt": 19,
    "Augsburg": 16,
    "Bayern Münih": 5,
    "St. Pauli": 20,
    "Holstein Kiel": 720,
    "RB Leipzig": 721,
    "Freiburg": 17,
    "Werder Bremen": 12,
    "Hoffenheim": 2,
    "Stuttgart": 10,
    "Bochum": 36,
    "Wolfsburg": 11,

    # Serie A
    "Milan": 98,
    "Monza": 5911,
    "Fiorentina": 99,
    "Roma": 100,
    "Atalanta": 102,
    "Bologna": 103,
    "Cagliari": 104,
    "Como": 7397,
    "Empoli": 445,
    "Inter": 108,
    "Genoa": 107,
    "Verona": 450,
    "Juventus": 109,
    "Parma": 112,
    "Lazio": 110,
    "Napoli": 113,
    "Torino": 586,
    "Lecce": 5890,
    "Udinese": 115,
    "Venezia": 454,

    # Ligue 1
    "Auxerre": 519,
    "Monaco": 548,
    "Saint-Étienne": 527,
    "Angers": 532,
    "Nantes": 543,
    "Le Havre": 533,
    "Lille": 521,
    "Montpellier": 518,
    "Nice": 522,
    "Lyon": 523,
    "Marseille": 516,
    "PSG": 524,
    "Strasbourg": 576,
    "Lens": 546,
    "Brest": 512,
    "Rennes": 529,
    "Reims": 547,
    "Toulouse": 511,

    # Eredivisie
    "Ajax": 678,
    "AZ Alkmaar": 682,
    "Almere City": 1911,
    "Groningen": 677,
    "Twente": 666,
    "Utrecht": 676,
    "Feyenoord": 675,
    "Fortuna Sittard": 1920,
    "Go Ahead Eagles": 718,
    "Heracles": 671,
    "NAC Breda": 681,
    "NEC": 1915,
    "PEC Zwolle": 684,
    "PSV": 674,
    "RKC Waalwijk": 683,
    "Heerenveen": 673,
    "Sparta Rotterdam": 6806,
    "Willem II": 672,

    # Primeira Liga
    "AVS": 10340,
    "Boavista": 810,
    "Nacional": 5529,
    "Santa Clara": 5530,
    "Estrela Amadora": 9136,
    "Casa Pia": 6618,
    "Arouca": 712,
    "Famalicao": 5531,
    "Porto": 503,
    "Estoril": 582,
    "Gil Vicente": 5533,
    "Moreirense": 583,
    "Rio Ave": 496,
    "Farense": 5602,
    "Benfica": 1903,
    "Braga": 5613,
    "Sporting CP": 498,
    "Vitoria SC": 5543,

    # Championship
    "Blackburn": 59,
    "Bristol City": 387,
    "Burnley": 328,
    "Cardiff": 715,
    "Coventry": 1076,
    "Derby County": 342,
    "Hull City": 322,
    "Leeds": 341,
    "Luton": 389,
    "Middlesbrough": 343,
    "Millwall": 384,
    "Norwich": 68,
    "Oxford United": 1082,
    "Plymouth": 1138,
    "Portsmouth": 325,
    "Preston": 1081,
    "QPR": 69,
    "Sheffield United": 356,
    "Sheffield Wednesday": 345,
    "Stoke": 70,
    "Sunderland": 71,
    "Swansea": 72,
    "Watford": 346,
    "West Brom": 74
}

def get_team_id(team_name):
    """Takım adından ID'sini bulur"""
    try:
        print(f"\nTakım ID'si aranıyor: {team_name}")
        
        # Takım ismini normalize et
        normalized_name = team_name.lower()
        normalized_name = normalized_name.replace("fc", "").replace("calcio", "").strip()
        
        # TEAM_ID_MAPPING'den takım ID'sini bul
        for mapped_name, team_id in TEAM_ID_MAPPING.items():
            mapped_normalized = mapped_name.lower()
            
            # Tam eşleşme veya içerme kontrolü
            if (normalized_name == mapped_normalized or 
                normalized_name in mapped_normalized or 
                mapped_normalized in normalized_name):
                print(f"Takım eşleşti: {team_name} -> {mapped_name} (ID: {team_id})")
                return team_id
        
        print(f"Takım bulunamadı: {team_name}")
        return None
        
    except Exception as e:
        print(f"Takım ID bulma hatası: {str(e)}")
        return None

def get_team_league(team_name):
    league_mappings = {
        "Premier League": [
            "AFC Bournemouth", "Arsenal", "Aston Villa", "Brentford", "Brighton",
            "Chelsea", "Crystal Palace", "Everton", "Fulham", "Ipswich",
            "Leicester", "Liverpool", "Manchester City", "Manchester United",
            "Newcastle", "Nottingham Forest", "Southampton", "Tottenham",
            "West Ham", "Wolves"
        ],
        "La Liga": [
            "Athletic Bilbao", "Osasuna", "Leganes", "Atletico Madrid", "Alaves",
            "Barcelona", "Getafe", "Girona", "Celta Vigo", "Espanyol",
            "Mallorca", "Rayo Vallecano", "Real Betis", "Real Madrid",
            "Real Sociedad", "Real Valladolid", "Sevilla", "Las Palmas",
            "Valencia", "Villarreal"
        ],
        "Bundesliga": [
            "Heidenheim", "Union Berlin", "Mainz", "Leverkusen", "Dortmund",
            "Mönchengladbach", "Eintracht Frankfurt", "Augsburg", "Bayern Münih",
            "St. Pauli", "Holstein Kiel", "RB Leipzig", "Freiburg",
            "Werder Bremen", "Hoffenheim", "Stuttgart", "Bochum", "Wolfsburg"
        ],
        "Serie A": [
            "Milan", "Monza", "Fiorentina", "Roma", "Atalanta", "Bologna",
            "Cagliari", "Como", "Empoli", "Inter", "Genoa", "Verona",
            "Juventus", "Parma", "Lazio", "Napoli", "Torino", "Lecce",
            "Udinese", "Venezia"
        ],
        "Ligue 1": [
            "Auxerre", "Monaco", "Saint-Étienne", "Angers", "Nantes",
            "Le Havre", "Lille", "Montpellier", "Nice", "Lyon", "Marseille",
            "PSG", "Strasbourg", "Lens", "Brest", "Rennes", "Reims", "Toulouse"
        ],
        "Eredivisie": [
            "Ajax", "AZ Alkmaar", "Almere City", "Groningen", "Twente",
            "Utrecht", "Feyenoord", "Fortuna Sittard", "Go Ahead Eagles",
            "Heracles", "NAC Breda", "NEC", "PEC Zwolle", "PSV",
            "RKC Waalwijk", "Heerenveen", "Sparta Rotterdam", "Willem II"
        ],
        "Primeira Liga": [
            "AVS", "Boavista", "Nacional", "Santa Clara", "Estrela Amadora",
            "Casa Pia", "Arouca", "Famalicao", "Porto", "Estoril",
            "Gil Vicente", "Moreirense", "Rio Ave", "Farense", "Benfica",
            "Braga", "Sporting CP", "Vitoria SC"
        ],
        "Championship": [
            "Blackburn", "Bristol City", "Burnley", "Cardiff", "Coventry",
            "Derby County", "Hull City", "Leeds", "Luton", "Middlesbrough",
            "Millwall", "Norwich", "Oxford United", "Plymouth", "Portsmouth",
            "Preston", "QPR", "Sheffield United", "Sheffield Wednesday",
            "Stoke", "Sunderland", "Swansea", "Watford", "West Brom"
        ]
    }
    
    for league, teams in league_mappings.items():
        if team_name in teams:
            return league
    return "Diğer" 