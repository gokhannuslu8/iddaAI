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
    1779: "BSA"  # Cuiabá
} 