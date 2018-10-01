import sqlite3 as dbms
import json


class SessionManager:
    def __init__(self):
        self.initDatabase()

    # define sqlite DB name
    db = 'skill.db'

    queries = {
        # session queries
        "cre_session": "CREATE TABLE IF NOT EXISTS Session(id INT, name TEXT, node TEXT)",
        "sel_session": "SELECT node FROM Session WHERE name=?",
        "ins_session": "INSERT INTO Session VALUES(?, ?, ?)",
        "upd_session": "UPDATE Session SET node=? WHERE name=?",
        "del_session": "DELETE FROM Session WHERE name=?",

        # general queries
        "cre_general": "CREATE TABLE IF NOT EXISTS General(id INT, key TEXT, value TEXT)",
        "sel_general": "SELECT value FROM General WHERE key=?",
        "ins_general": "INSERT INTO General VALUES(?, ?, ?)",
        "upd_general": "UPDATE General SET value=? WHERE key=?"
    }

    # creates db tables if not existing
    def initDatabase(self):
        con = dbms.connect(self.db)
        with con:
            cur = con.cursor()
            cur.execute(self.queries.get("cre_session"))
            cur.execute(self.queries.get("cre_general"))
        return


    # check if any user is logged in
    def checkLoggedIn(self):
        con = dbms.connect(self.db)
        with con:
            con.row_factory = dbms.Row
            cur = con.cursor()
            cur.execute(self.queries.get("sel_general"), ("loggedin",))
            row = cur.fetchone()
            if row == None or row["value"] == "None":
                return False, None
            else:
                return True, row["value"]

    # loads session from db
    def loadSession(self, name):
        con = dbms.connect(self.db)
        with con:
            con.row_factory = dbms.Row
            cur = con.cursor()
            cur.execute(self.queries.get("sel_session"), (name,))
            row = cur.fetchone()
            if row == None or row["node"] == "None":
                return None
            else:
                return row

    # saves session to db
    def saveSession(self, session):
        name = session['name']
        sessionJson = json.dumps(session)
        con = dbms.connect(self.db)
        with con:
            cur = con.cursor()
            cur.execute(self.queries.get("sel_session"), (name,))
            # if entry not exists then get row id and insert session
            if cur.fetchone() == None:
                rowId = cur.lastrowid
                if rowId == None:
                    rowId = 1
                else:
                    rowId = rowId + 1
                cur.execute(self.queries.get("ins_session"), (rowId, name, sessionJson))
            # if entry exists then update session in row
            else:
                cur.execute(self.queries.get("upd_session"), (sessionJson, name))
        return

    # deletes session from db
    def delSession(self, name):
        con = dbms.connect(self.db)
        with con:
            cur = con.cursor()
            cur.execute(self.queries.get("del_session"), (name,))
            con.commit()
        return

    # logs in a specific user by name
    def login(self, name):
        con = dbms.connect(self.db)
        with con:
            cur = con.cursor()
            cur.execute(self.queries.get("sel_general"), ("loggedin",))
            if cur.fetchone() == None:
                rowId = cur.lastrowid
                if rowId == None:
                    rowId = 1
                else:
                    rowId = rowId + 1
                cur.execute(self.queries.get("ins_general"), (rowId, "loggedin", name))
            else:
                cur.execute(self.queries.get("upd_general"), (name, "loggedin"))
        return

    # logs out any user
    def logout(self):
        self.login("None")
        return
