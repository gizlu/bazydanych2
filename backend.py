import sqlite3
import hashlib
import os
from contextlib import closing

DB_PATH = "spell_rental.sqlite"
SALT_BITS = 32
HASH_BITS = 128

def tobytes(s):
    if isinstance(s, str): return str.encode(s, "utf-8")
    else: return s # assume that s is bytes already

def makehash(password, salt):
    # params from https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html#scrypt
    return hashlib.scrypt(tobytes(password), salt=tobytes(salt), n=2**13, r=8, p=5, dklen=HASH_BITS//8)

def opendb():
    con = sqlite3.connect(DB_PATH)
    con.create_function("MAKE_HASH", 2, makehash)
    return con

def err(*args, **kwargs):
    print(*args, **kwargs)
    exit(1)

def register(username, password, isCurator=False):
    salt = os.urandom(SALT_BITS//8)
    con = opendb()
    with closing(con.cursor()) as cursor:
        # cursor.execute("INSERT INTO wizards(login, passHash, passSalt, isCurator) VALUES (?, ?, ?, ?)",
        #                      (username, makehash(password, salt), salt, isCurator))
        cursor.execute("INSERT INTO wizards(login, passHash, passSalt, isCurator) VALUES (?, MAKE_HASH(?,?), ?, ?)",
                             (username, password, salt, salt, isCurator))
        user_id = cursor.lastrowid
    con.commit()
    return Session(con, user_id)

def login(username, password):
    con = opendb()
    result = con.execute(
        "SELECT id FROM wizards WHERE login == ? AND passHash == MAKE_HASH(?, passSalt)", 
        (username, password)
    ).fetchone()

    if(result):
        user_id=result[0]
        return Session(con, user_id)
    else:
        err("Unable to log in")

    
class Session:
    def __init__(self, con, user_id):
        self.con = con
        self.user_id = user_id

    def isCurator(self):
        result = self.con.execute("SELECT isCurator FROM wizards WHERE id = ?", (self.user_id,)).fetchone()
        assert(result is not None)
        return result[0]

    def getRank(self):
        result = self.con.execute("SELECT rankId FROM wizards WHERE id = ?", (self.user_id,)).fetchone()
        assert(result is not None)
        return result[0]

    def getUserSummary(self):
        result = self.con.execute("""
            SELECT login, ranks.name, isCurator, COUNT(rentals.id), ranks.rentalLimit FROM wizards
            LEFT JOIN ranks ON wizards.rankId=ranks.id
            LEFT JOIN rentals ON wizards.id=rentals.wizardId
            GROUP BY wizards.id
            HAVING wizards.id = ?
            """,
            (self.user_id,)
        ).fetchone()

        assert(result is not None)
        return result
 
    def listWizards(self):
        result = self.con.execute("""SELECT wizards.id, login, ranks.name FROM wizards
                                JOIN ranks ON wizards.rankId=ranks.id
                                ORDER BY login
                                """).fetchall()
        return result


    def getSpellData(self, spellId):
        with closing(self.con.cursor()) as cursor:
            result = cursor.execute("""
            SELECT spells.name, description, ranks.name as requiredRankName, ranks.id as requiredRankId,
            consumedMana, wizards.login as ownerLogin, isApproved,
               (SELECT COUNT(*) FROM rentals WHERE spellId=? AND wizardId=?) as isRentedByUser,
               ownerWizardId=? as isUserOwner
            FROM spells
            JOIN wizards on spells.ownerWizardId=wizards.id
            JOIN ranks on spells.requiredRankId=ranks.id
            WHERE spells.id == ?
            """, (spellId, self.user_id, self.user_id, spellId)).fetchone()
            return result
        
    def listAvailableSpells(self):
        # returns list of approved spells that suit user rank
        return self.con.execute("""SELECT id, name, description FROM spells
                           WHERE (isApproved AND
                               requiredRankId <= (SELECT rankId FROM wizards WHERE id = ?)) OR ownerWizardId = ?
                           ORDER BY name""", (self.user_id,self.user_id ))

    def searchAvailableSpells(self, pattern):
        # TODO
        return self.con.execute("""SELECT id, name, description FROM spells
                           WHERE isApproved AND
                               requiredRankId <= (SELECT rankId FROM wizards WHERE id = ?)
                           ORDER BY name""")

    def listSpellsToApprove(self):
        return self.con.execute(
                        "SELECT id, name, description FROM spells WHERE not isApproved ORDER BY name")

    def listAllSpells(self):
        return self.con.execute("SELECT id, name, description FROM spells ORDER BY name")

    def listRanks(self):
        with closing(self.con.cursor()) as cursor:
            cursor.execute("SELECT name, id FROM ranks ORDER BY id")
            return {rankName : rankId for rankName, rankId in cursor}

    def setRank(self, wizard_id, rank_id):
        self.con.execute("UPDATE wizards SET rankId = ? WHERE id = ?", (rank_id, wizard_id))
        self.con.commit()

    # def getRentedSpells(self):
    #     with closing(self.con.cursor()) as cursor:
    #         cursor.execute("""
    #         SELECT spells.name,  FROM wizards
    #         LEFT JOIN ranks ON wizards.rankId=ranks.id
    #         WHERE wizards.id = ?
    #         """, (self.user_id,))
    #         cursor = self.con.cursor()
    #         cursor.execute("SELECT * FROM spells WHERE requiredRankId <= rankID")
    #         return cursor.fetchall

    def getRentedSpells(self):
        with closing(self.con.cursor()) as cursor:
            cursor.execute("""
            SELECT spells.name, rentals.startTimestamp, rentals.endTimestamp
            FROM rentals
            JOIN spells ON rentals.spellId = spells.id
            WHERE rentals.wizardId = ?
            ORDER BY rentals.startTimestamp
            """, (self.user_id,))
            return cursor.fetchall()


    def getOwnedSpells(self):
        # TODO
        return self.con.execute("SELECT * FROM spells WHERE requiredRankId <= rankID").fetchall()

    def approveSpell(self, spellId):
        self.con.execute("UPDATE spells SET isApproved = 1 WHERE id = ?", (spellId,))
        self.con.commit()

    def removeSpell(self, spellId):
        self.con.execute("""
                         DELETE FROM rentals WHERE spellId = ?;
                         DELETE FROM spells WHERE id = ?;
                         """, (spellId, spellId))
        self.con.commit()

    def unrentSpell(self, spellId):
        self.con.execute("DELETE FROM rentals WHERE spellId = ? AND wizardId = ?", (spellId, self.user_id))
        self.con.commit()

    # def updateSpell(self, id, name, description, requiredRankId, consumedMana, rentalTerms):
    #     # TODO
    #     pass
    def updateSpell(self, spellId, name, description, requiredRankId, consumedMana, rentalTerms):
        with closing(self.con.cursor()) as cursor:
            cursor.execute("""
        UPDATE spells
        SET name = ?, description = ?, requiredRankId = ?, consumedMana = ?
        WHERE id = ?
        """, (name, description, requiredRankId, consumedMana, spellId))
            self.con.commit()


    def rentSpell(self, spellId, days):
        self.con.execute("""
        INSERT INTO rentals(wizardId, spellId, startTimestamp, endTimestamp)
        VALUES(?,?,unixepoch(), unixepoch('now',format('+%d day', ?)))
        """, (self.user_id, spellId, days)
        )
        self.con.commit()
    
    def addSpell(self, name, desc, requiredRankId, consumedMana):
        self.con.execute("""
        INSERT INTO spells(name, description, requiredRankId, consumedMana, ownerWizardId)
        VALUES (?,?,?,?,?)
        """,  (name, desc, requiredRankId, consumedMana, self.user_id,)
        )
        self.con.commit()

