#!/bin/sh
sqlite3 spell_rental.sqlite <<'EOF'
BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "spells" (
	"id" INTEGER,
	"name" TEXT,
	"description" TEXT,
	"requiredRankId" INTEGER,
	"consumedMana" INTEGER,
  "ownerWizardId" INTEGER,
  "isApproved" INTEGER DEFAULT 0, -- set to 1 by curator
	PRIMARY KEY("id")
);

CREATE TABLE IF NOT EXISTS "ranks" (
	"id" INTEGER PRIMARY KEY,
	"name" TEXT UNIQUE,
	"rentalLimit" INTEGER
);

INSERT INTO ranks VALUES
	(0, 'Czeladnik', 3),
	(1, 'Adept', 6),
	(2, 'Mistrz', 6),
	(3, 'Mag Wysoki', 9),
	(4, 'Arcymag', 12)
;

CREATE TABLE IF NOT EXISTS "wizards" (
	"id" INTEGER PRIMARY KEY,
  "login" TEXT UNIQUE,
  "passHash" BLOB, -- scrypt hash
  "passSalt" BLOB, -- 16 losowych bajtów
	"rankId" INTEGER DEFAULT 0,
	"isCurator" INTEGER DEFAULT 0,
  FOREIGN KEY("rankId") REFERENCES "ranks"("id")
);

CREATE TABLE IF NOT EXISTS "rentals" (
	"id" INTEGER PRIMARY KEY,
	"wizardId" INTEGER,
	"spellId" INTEGER,
	"startTimestamp" INTEGER, /* unix timestamp */
	"endTimestamp" INTEGER,
  FOREIGN KEY("wizardId") REFERENCES "wizards"("id"),
  FOREIGN KEY("spellId") REFERENCES "spells"("id")
);
CREATE INDEX IF NOT EXISTS spells_index ON spells(name, isApproved, requiredRankId, ownerWizardId); -- for spells listing and search
COMMIT TRANSACTION;
EOF

python -c '
import backend, os, getpass


print("Baza potrzebuje chociaż jednego kustosza. Utwórz mu konto")
backend.register(input("nazwa użytkownika: "), getpass.getpass("hasło: "), isCurator=True)



# Add few sample wizards
sarumun = backend.register("Sarumun", b"apud12")
sarumun.addSpell(
	"lodowy podmuch dpy",
	"""Proste zaklęcie atakujące, będące w stanie zabić jedną osobę
	Nie da się go zablokować toporem""",
	sarumun.listRanks()["Adept"],
	5,
)

alzur = backend.register("Alzur", os.urandom(64))
alzur.addSpell(
	"Piorun Alzura",
	"Zaklęcie wywołujące potężny piorun mogący zabić kilka osób.",
	alzur.listRanks()["Mag Wysoki"],
	80,
)

tris = backend.register("Tris", b"apud12")
tris.addSpell(
	"Niszczące Gradobicie Merigold",
	"""Destrukcyjne zaklęcie o olbrzymiej sile rażenia, powstałe nieumyślnie na podstawie Piorunu Alzura.
Ponieważ nigdy nie udało się tego zaklęcia powtórzyć, nie może być ono oficjalnie zarejestrowane.""",
	tris.listRanks()["Arcymag"],
	200,
)
'
