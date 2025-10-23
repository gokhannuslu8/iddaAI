# Lig ID'leri
LEAGUE_IDS = {
    "PL": "Premier League",    # İngiltere Premier Lig
    "PD": "La Liga",          # İspanya La Liga
    "BL1": "Bundesliga",      # Almanya Bundesliga
    "SA": "Serie A",          # İtalya Serie A
    "FL1": "Ligue 1",         # Fransa Ligue 1
    "DED": "Eredivisie",      # Hollanda Eredivisie
    "PPL": "Primeira Liga",   # Portekiz Primeira Liga
    "BSA": "Brasileirão",     # Brezilya Serie A
    "ELC": "Championship",     # İngiltere Championship
    "CL": "Champions League",  # UEFA Champions League
    "EL": "Europa League"      # UEFA Europa League
}

# Takım ID'lerinin hangi lige ait olduğunu gösteren eşleştirme
TEAM_ID_TO_LEAGUE = {
    # Premier League Takımları
    65: "PL",  # Manchester City
    57: "PL",  # Arsenal
    66: "PL",  # Manchester United
    67: "PL",  # Newcastle
    64: "PL",  # Liverpool
    397: "PL", # Brighton
    58: "PL",  # Aston Villa
    73: "PL",  # Tottenham
    402: "PL", # Brentford
    63: "PL",  # Fulham
    354: "PL", # Crystal Palace
    61: "PL",  # Chelsea
    76: "PL",  # Wolves
    563: "PL", # West Ham
    349: "PL", # Bournemouth
    351: "PL", # Nottingham Forest
    62: "PL",  # Everton
    389: "PL", # Luton
    356: "PL", # Sheffield United
    328: "PL", # Burnley

    # La Liga Takımları
    86: "PD",  # Real Madrid
    81: "PD",  # Barcelona
    78: "PD",  # Atletico Madrid
    77: "PD",  # Athletic Bilbao
    92: "PD",  # Real Sociedad
    90: "PD",  # Real Betis
    95: "PD",  # Valencia
    298: "PD", # Girona
    79: "PD",  # Osasuna
    94: "PD",  # Villarreal
    87: "PD",  # Rayo Vallecano
    559: "PD", # Sevilla
    275: "PD", # Las Palmas
    82: "PD",  # Getafe
    263: "PD", # Alaves
    89: "PD",  # Mallorca
    558: "PD", # Celta Vigo

    # Bundesliga Takımları
    5: "BL1",   # Bayern Münih
    3: "BL1",   # Leverkusen
    10: "BL1",  # Stuttgart
    721: "BL1", # RB Leipzig
    4: "BL1",   # Dortmund
    2: "BL1",   # Hoffenheim
    19: "BL1",  # Eintracht Frankfurt
    17: "BL1",  # Freiburg
    11: "BL1",  # Wolfsburg
    16: "BL1",  # Augsburg
    18: "BL1",  # Mönchengladbach
    12: "BL1",  # Werder Bremen
    28: "BL1",  # Union Berlin
    36: "BL1",  # Bochum
    15: "BL1",  # Mainz

    # Serie A Takımları
    108: "SA", # Inter
    109: "SA", # Juventus
    98: "SA",  # Milan
    113: "SA", # Napoli
    99: "SA",  # Fiorentina
    102: "SA", # Atalanta
    100: "SA", # Roma
    103: "SA", # Bologna
    110: "SA", # Lazio
    586: "SA", # Torino
    107: "SA", # Genoa
    115: "SA", # Udinese
    104: "SA", # Cagliari
    445: "SA", # Empoli
    450: "SA", # Verona

    # Ligue 1 Takımları
    524: "FL1", # PSG
    522: "FL1", # Nice
    548: "FL1", # Monaco
    512: "FL1", # Brest
    521: "FL1", # Lille
    546: "FL1", # Lens
    516: "FL1", # Marseille
    547: "FL1", # Reims
    523: "FL1", # Lyon
    576: "FL1", # Strasbourg
    529: "FL1", # Rennes
    511: "FL1", # Toulouse
    518: "FL1", # Montpellier
    543: "FL1", # Nantes

    # Championship Takımları
    338: "ELC", # Leicester
    345: "ELC", # Ipswich
    341: "ELC", # Leeds
    340: "ELC", # Southampton
    349: "ELC", # West Brom
    322: "ELC", # Hull City
    1076: "ELC", # Coventry
    351: "ELC", # Sunderland
    1081: "ELC", # Preston
    343: "ELC", # Middlesbrough
    715: "ELC", # Cardiff
    387: "ELC", # Bristol City
    346: "ELC", # Watford
    342: "ELC", # QPR
    384: "ELC", # Millwall

    # Eredivisie Takımları
    674: "DED", # PSV
    675: "DED", # Feyenoord
    677: "DED", # AZ Alkmaar
    676: "DED", # Twente
    678: "DED", # Ajax
    684: "DED", # Sparta Rotterdam
    681: "DED", # Heerenveen
    1915: "DED", # Excelsior
    683: "DED", # Heracles

    # Primeira Liga Takımları
    498: "PPL", # Sporting CP
    503: "PPL", # Porto
    496: "PPL", # Braga

    # Brasileirão Takımları
    1777: "BSA", # Athletico-PR
    1779: "BSA", # Cuiabá

    # UEFA Champions League Takımları (2024-25) - Benzersiz ID'ler
    2001: "CL", # Galatasaray SK
    2002: "CL", # Fenerbahçe SK
    86: "CL",   # Real Madrid CF
    81: "CL",   # FC Barcelona
    78: "CL",   # Club Atlético de Madrid
    92: "CL",   # Real Sociedad de Fútbol
    298: "CL",  # Girona FC
    65: "CL",   # Manchester City FC
    57: "CL",   # Arsenal FC
    64: "CL",   # Liverpool FC
    58: "CL",   # Aston Villa FC
    5: "CL",    # FC Bayern München
    3: "CL",    # Bayer 04 Leverkusen
    10: "CL",   # VfB Stuttgart
    721: "CL",  # RB Leipzig
    4: "CL",    # Borussia Dortmund
    19: "CL",   # Eintracht Frankfurt
    98: "CL",   # AC Milan
    108: "CL",  # FC Internazionale Milano
    109: "CL",  # Juventus FC
    102: "CL",  # Atalanta BC
    103: "CL",  # Bologna FC 1909
    524: "CL",  # Paris Saint-Germain FC
    548: "CL",  # AS Monaco FC
    521: "CL",  # Lille OSC
    512: "CL",  # Stade Brestois 29
    674: "CL",  # PSV
    675: "CL",  # Feyenoord Rotterdam
    678: "CL",  # AFC Ajax
    498: "CL",  # Sporting Clube de Portugal
    1903: "CL", # Sport Lisboa e Benfica
    503: "CL",  # FC Porto
    5613: "CL", # Sporting Clube de Braga
    1003: "CL", # Celtic FC
    1004: "CL", # Rangers FC
    1005: "CL", # Club Brugge KV
    1006: "CL", # Union Saint-Gilloise
    2007: "CL", # Bodo/Glimt
    1008: "CL", # Shakhtar Donetsk
    1009: "CL", # Dinamo Zagreb
    1010: "CL", # Red Bull Salzburg
    1011: "CL", # FC Copenhagen
    1012: "CL", # Young Boys
    1013: "CL"  # Slavia Praha
} 