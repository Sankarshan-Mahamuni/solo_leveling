CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Username TEXT NOT NULL UNIQUE,
    Password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT NOT NULL UNIQUE,
    Age INTEGER NOT NULL,
    Height INTEGER NOT NULL,
    Weight INTEGER NOT NULL,
    Email TEXT NOT NULL,
    Level INTEGER NOT NULL,
    Xp INTEGER NOT NULL,
    Strength_level INTEGER NOT NULL,
    Strength_points INTEGER NOT NULL,
    Intelligence_level INTEGER NOT NULL,
    Intelligence_points INTEGER NOT NULL,
    Imotional_control INTEGER NOT NULL,
    Meditation_points INTEGER NOT NULL
);


