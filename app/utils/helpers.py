TEAM_ID_MAPPING = {
    # Premier League (Güncel 2025-26)
    "Arsenal FC": 57,
    "Aston Villa FC": 58,
    "Chelsea FC": 61,
    "Everton FC": 62,
    "Fulham FC": 63,
    "Liverpool FC": 64,
    "Manchester City FC": 65,
    "Manchester United FC": 66,
    "Newcastle United FC": 67,
    "Sunderland AFC": 71,
    "Tottenham Hotspur FC": 73,
    "Wolverhampton Wanderers FC": 76,
    "Burnley FC": 328,
    "Leeds United FC": 341,
    "Nottingham Forest FC": 351,
    "Crystal Palace FC": 354,
    "Brighton & Hove Albion FC": 397,
    "Brentford FC": 402,
    "West Ham United FC": 563,
    "AFC Bournemouth": 1044,

    # Bundesliga (Güncel 2025-26)
    "1. FC Köln": 1,
    "TSG 1899 Hoffenheim": 2,
    "Bayer 04 Leverkusen": 3,
    "Borussia Dortmund": 4,
    "FC Bayern München": 5,
    "Hamburger SV": 7,
    "VfB Stuttgart": 10,
    "VfL Wolfsburg": 11,
    "SV Werder Bremen": 12,
    "1. FSV Mainz 05": 15,
    "FC Augsburg": 16,
    "SC Freiburg": 17,
    "Borussia Mönchengladbach": 18,
    "Eintracht Frankfurt": 19,
    "FC St. Pauli 1910": 20,
    "1. FC Union Berlin": 28,
    "1. FC Heidenheim 1846": 44,
    "RB Leipzig": 721,

    # La Liga (Güncel 2025-26)
    "Athletic Club": 77,
    "Club Atlético de Madrid": 78,
    "CA Osasuna": 79,
    "RCD Espanyol de Barcelona": 80,
    "FC Barcelona": 81,
    "Getafe CF": 82,
    "Real Madrid CF": 86,
    "Rayo Vallecano de Madrid": 87,
    "Levante UD": 88,
    "RCD Mallorca": 89,
    "Real Betis Balompié": 90,
    "Real Sociedad de Fútbol": 92,
    "Villarreal CF": 94,
    "Valencia CF": 95,
    "Deportivo Alavés": 263,
    "Elche CF": 285,
    "Girona FC": 298,
    "RC Celta de Vigo": 558,
    "Sevilla FC": 559,
    "Real Oviedo": 1048,

    # Serie A (Güncel 2025-26)
    "AC Milan": 98,
    "ACF Fiorentina": 99,
    "AS Roma": 100,
    "Atalanta BC": 102,
    "Bologna FC 1909": 103,
    "Cagliari Calcio": 104,
    "Genoa CFC": 107,
    "FC Internazionale Milano": 108,
    "Juventus FC": 109,
    "SS Lazio": 110,
    "Parma Calcio 1913": 112,
    "SSC Napoli": 113,
    "Udinese Calcio": 115,
    "Hellas Verona FC": 450,
    "US Cremonese": 457,
    "US Sassuolo Calcio": 471,
    "AC Pisa 1909": 487,
    "Torino FC": 586,
    "US Lecce": 5890,
    "Como 1907": 7397,

    # Ligue 1 (Güncel 2025-26)
    "Toulouse FC": 511,
    "Stade Brestois 29": 512,
    "Olympique de Marseille": 516,
    "AJ Auxerre": 519,
    "Lille OSC": 521,
    "OGC Nice": 522,
    "Olympique Lyonnais": 523,
    "Paris Saint-Germain FC": 524,
    "FC Lorient": 525,
    "Stade Rennais FC 1901": 529,
    "Angers SCO": 532,
    "Le Havre AC": 533,
    "FC Nantes": 543,
    "FC Metz": 545,
    "Racing Club de Lens": 546,
    "AS Monaco FC": 548,
    "RC Strasbourg Alsace": 576,
    "Paris FC": 1045,

    # Eredivisie (Güncel 2025-26)
    "FC Twente '65": 666,
    "SBV Excelsior": 670,
    "Heracles Almelo": 671,
    "SC Heerenveen": 673,
    "PSV": 674,
    "Feyenoord Rotterdam": 675,
    "FC Utrecht": 676,
    "FC Groningen": 677,
    "AFC Ajax": 678,
    "NAC Breda": 681,
    "AZ": 682,
    "PEC Zwolle": 684,
    "Go Ahead Eagles": 718,
    "Telstar 1963": 1912,
    "NEC": 1915,
    "FC Volendam": 1919,
    "Fortuna Sittard": 1920,
    "Sparta Rotterdam": 6806,

    # Primeira Liga (Güncel 2025-26)
    "Rio Ave FC": 496,
    "Sporting Clube de Portugal": 498,
    "FC Porto": 503,
    "GD Estoril Praia": 582,
    "Moreirense FC": 583,
    "FC Arouca": 712,
    "CD Tondela": 1049,
    "Sport Lisboa e Benfica": 1903,
    "CD Nacional": 5529,
    "CD Santa Clara": 5530,
    "FC Famalicão": 5531,
    "Gil Vicente FC": 5533,
    "Vitória SC": 5543,
    "Sporting Clube de Braga": 5613,
    "Casa Pia AC": 6618,
    "FC Alverca": 7822,
    "CF Estrela da Amadora": 9136,
    "AVS": 10340,

    # Championship (Güncel 2025-26)
    "Blackburn Rovers FC": 59,
    "Norwich City FC": 68,
    "Queens Park Rangers FC": 69,
    "Stoke City FC": 70,
    "Swansea City AFC": 72,
    "West Bromwich Albion FC": 74,
    "Hull City AFC": 322,
    "Portsmouth FC": 325,
    "Birmingham City FC": 332,
    "Leicester City FC": 338,
    "Southampton FC": 340,
    "Derby County FC": 342,
    "Middlesbrough FC": 343,
    "Sheffield Wednesday FC": 345,
    "Watford FC": 346,
    "Charlton Athletic FC": 348,
    "Ipswich Town FC": 349,
    "Sheffield United FC": 356,
    "Millwall FC": 384,
    "Bristol City FC": 387,
    "Wrexham AFC": 404,
    "Coventry City FC": 1076,
    "Preston North End FC": 1081,
    "Oxford United FC": 1082
}

def get_team_id(team_name):
    """Takım adından ID'sini bulur - hem tam isim hem kısa isim destekler"""
    try:
        print(f"\nTakım ID'si aranıyor: {team_name}")
        
        # Özel eşleştirmeler (yaygın kullanılan isimler)
        special_mappings = {
            "Real Madrid": "Real Madrid CF",
            "Barcelona": "FC Barcelona", 
            "Atletico Madrid": "Club Atlético de Madrid",
            "Atleti": "Club Atlético de Madrid",
            "Man City": "Manchester City FC",
            "Man United": "Manchester United FC",
            "Bayern": "FC Bayern München",
            "Bayern München": "FC Bayern München",
            "Bayern Munich": "FC Bayern München",
            "PSG": "Paris Saint-Germain FC",
            "Paris SG": "Paris Saint-Germain FC",
            "Monaco": "AS Monaco FC",
            "Lyon": "Olympique Lyonnais",
            "Marseille": "Olympique de Marseille"
        }
        
        # Özel eşleştirme kontrolü
        if team_name in special_mappings:
            mapped_name = special_mappings[team_name]
            if mapped_name in TEAM_ID_MAPPING:
                print(f"Özel eşleştirme: {team_name} -> {mapped_name} (ID: {TEAM_ID_MAPPING[mapped_name]})")
                return TEAM_ID_MAPPING[mapped_name]
        
        # Önce tam eşleşme dene
        if team_name in TEAM_ID_MAPPING:
            print(f"Tam eşleşme bulundu: {team_name} -> ID: {TEAM_ID_MAPPING[team_name]}")
            return TEAM_ID_MAPPING[team_name]
        
        # Takım ismini normalize et
        normalized_name = team_name.lower().strip()
        
        # TEAM_ID_MAPPING'den takım ID'sini bul (esnek eşleşme)
        for mapped_name, team_id in TEAM_ID_MAPPING.items():
            mapped_normalized = mapped_name.lower()
            
            # Tam eşleşme
            if normalized_name == mapped_normalized:
                print(f"Tam eşleşme: {team_name} -> {mapped_name} (ID: {team_id})")
                return team_id
            
            # Kısa isim eşleşmesi (örn: "Real Madrid" -> "Real Madrid CF")
            # Ama önce tam kelime eşleşmesi kontrol et
            if (normalized_name in mapped_normalized and 
                len(normalized_name) >= 5 and
                # Kelime sınırları kontrol et (tam kelime eşleşmesi)
                (mapped_normalized.startswith(normalized_name) or 
                 mapped_normalized.endswith(normalized_name) or
                 f" {normalized_name} " in f" {mapped_normalized} ")):
                print(f"Kısa isim eşleşmesi: {team_name} -> {mapped_name} (ID: {team_id})")
                return team_id
            
            # Tam isim içinde kısa isim (örn: "Barcelona" -> "FC Barcelona")
            if (mapped_normalized in normalized_name and 
                len(mapped_normalized) >= 5):
                print(f"İçerme eşleşmesi: {team_name} -> {mapped_name} (ID: {team_id})")
                return team_id
        
        print(f"Takım bulunamadı: {team_name}")
        print("Mevcut takımlar:")
        for name in list(TEAM_ID_MAPPING.keys())[:10]:  # İlk 10 takımı göster
            print(f"  - {name}")
        return None
        
    except Exception as e:
        print(f"Takım ID bulma hatası: {str(e)}")
        return None

def get_team_league(team_name):
    """Takım adından ligini bulur - esnek eşleştirme ile"""
    
    # Önce tam takım adını bul
    actual_team_name = team_name
    
    # Özel eşleştirmeler (get_team_id ile aynı)
    special_mappings = {
        "Real Madrid": "Real Madrid CF",
        "Barcelona": "FC Barcelona", 
        "Atletico Madrid": "Club Atlético de Madrid",
        "Atleti": "Club Atlético de Madrid",
        "Man City": "Manchester City FC",
        "Man United": "Manchester United FC",
        "Bayern": "FC Bayern München",
        "Bayern München": "FC Bayern München",
        "Bayern Munich": "FC Bayern München",
        "PSG": "Paris Saint-Germain FC",
        "Paris SG": "Paris Saint-Germain FC",
        "Monaco": "AS Monaco FC",
        "Lyon": "Olympique Lyonnais",
        "Marseille": "Olympique de Marseille"
    }
    
    if team_name in special_mappings:
        actual_team_name = special_mappings[team_name]
    
    league_mappings = {
        "Premier League": [
            "Arsenal FC", "Aston Villa FC", "Chelsea FC", "Everton FC", "Fulham FC",
            "Liverpool FC", "Manchester City FC", "Manchester United FC", "Newcastle United FC", "Sunderland AFC",
            "Tottenham Hotspur FC", "Wolverhampton Wanderers FC", "Burnley FC", "Leeds United FC", "Nottingham Forest FC",
            "Crystal Palace FC", "Brighton & Hove Albion FC", "Brentford FC", "West Ham United FC", "AFC Bournemouth"
        ],
        "La Liga": [
            "Athletic Club", "Club Atlético de Madrid", "CA Osasuna", "RCD Espanyol de Barcelona", "FC Barcelona",
            "Getafe CF", "Real Madrid CF", "Rayo Vallecano de Madrid", "Levante UD", "RCD Mallorca", "Real Betis Balompié",
            "Real Sociedad de Fútbol", "Villarreal CF", "Valencia CF", "Deportivo Alavés", "Elche CF",
            "Girona FC", "RC Celta de Vigo", "Sevilla FC", "Real Oviedo"
        ],
        "Bundesliga": [
            "1. FC Köln", "TSG 1899 Hoffenheim", "Bayer 04 Leverkusen", "Borussia Dortmund", "FC Bayern München",
            "Hamburger SV", "VfB Stuttgart", "VfL Wolfsburg", "SV Werder Bremen", "1. FSV Mainz 05", "FC Augsburg",
            "SC Freiburg", "Borussia Mönchengladbach", "Eintracht Frankfurt", "FC St. Pauli 1910", "1. FC Union Berlin",
            "1. FC Heidenheim 1846", "RB Leipzig"
        ],
        "Serie A": [
            "AC Milan", "ACF Fiorentina", "AS Roma", "Atalanta BC", "Bologna FC 1909", "Cagliari Calcio",
            "Genoa CFC", "FC Internazionale Milano", "Juventus FC", "SS Lazio", "Parma Calcio 1913", "SSC Napoli",
            "Udinese Calcio", "Hellas Verona FC", "US Cremonese", "US Sassuolo Calcio", "AC Pisa 1909", "Torino FC",
            "US Lecce", "Como 1907"
        ],
        "Ligue 1": [
            "Toulouse FC", "Stade Brestois 29", "Olympique de Marseille", "AJ Auxerre", "Lille OSC", "OGC Nice",
            "Olympique Lyonnais", "Paris Saint-Germain FC", "FC Lorient", "Stade Rennais FC 1901", "Angers SCO",
            "Le Havre AC", "FC Nantes", "FC Metz", "Racing Club de Lens", "AS Monaco FC", "RC Strasbourg Alsace",
            "Paris FC"
        ],
        "Eredivisie": [
            "FC Twente '65", "SBV Excelsior", "Heracles Almelo", "SC Heerenveen", "PSV", "Feyenoord Rotterdam",
            "FC Utrecht", "FC Groningen", "AFC Ajax", "NAC Breda", "AZ", "PEC Zwolle", "Go Ahead Eagles",
            "Telstar 1963", "NEC", "FC Volendam", "Fortuna Sittard", "Sparta Rotterdam"
        ],
        "Primeira Liga": [
            "Rio Ave FC", "Sporting Clube de Portugal", "FC Porto", "GD Estoril Praia", "Moreirense FC",
            "FC Arouca", "CD Tondela", "Sport Lisboa e Benfica", "CD Nacional", "CD Santa Clara",
            "FC Famalicão", "Gil Vicente FC", "Vitória SC", "Sporting Clube de Braga", "Casa Pia AC",
            "FC Alverca", "CF Estrela da Amadora", "AVS"
        ],
        "Championship": [
            "Blackburn Rovers FC", "Norwich City FC", "Queens Park Rangers FC", "Stoke City FC", "Swansea City AFC",
            "West Bromwich Albion FC", "Hull City AFC", "Portsmouth FC", "Birmingham City FC", "Leicester City FC",
            "Southampton FC", "Derby County FC", "Middlesbrough FC", "Sheffield Wednesday FC", "Watford FC",
            "Charlton Athletic FC", "Ipswich Town FC", "Sheffield United FC", "Millwall FC", "Bristol City FC",
            "Wrexham AFC", "Coventry City FC", "Preston North End FC", "Oxford United FC"
        ]
    }
    
    # Önce tam eşleşme dene
    for league, teams in league_mappings.items():
        if actual_team_name in teams:
            return league
    
    # Esnek eşleştirme (kısa isimler için)
    normalized_name = actual_team_name.lower().strip()
    for league, teams in league_mappings.items():
        for team in teams:
            team_normalized = team.lower()
            if (normalized_name in team_normalized and len(normalized_name) >= 5):
                return league
    
    return "Diğer" 