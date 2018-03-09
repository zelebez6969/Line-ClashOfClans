# -*- coding: utf-8 -*-
import sys, time, random
import MySQLdb
from main_profile import cocapi

reload(sys)
sys.setdefaultencoding('utf-8')

db = MySQLdb.connect(host="localhost",user="root",passwd="passwd",db="cocapi")
db.autocommit(True)
cur = db.cursor()

g_coc = cocapi()

class commands:
    def __init__(self): #variables
        self.owner = "u5d5b406851db8c08a7107ca9b0d68d52"
        self.season_end = 1517201677
        self.rname = "-coc "
        self.letter_sealing_list = ["Letter sealing means that messages are encrypted and can't be read by the bot.\n",
                                    "If everyone in the group has it enabled, the bot won't work.\n",
                                    "Likewise, if you have it enabled, it won't work in pm.\n",
                                    "To disable it go to:\n->More\n->Settings\n->Privace\n and turn it off there."]
        self.set_message = "nothing rn"
        self.help_base = ["help","rname"]
        self.help_misc = ["season end",
                            "help",
                            "tag contact(s)",
                            "contacts off",
                            "message",
                            "@bye",
                            "IMPORTANT"]
        self.help_link = ["link me to #",
                            "unlink me",
                            "unlink me from all",
                            "unlink me from #",
                            "unlink me from number(s)"]
        self.help_show = ["show my #",
                            "show contact of #",
                            "show # of contact",
                            "show # of contacts",
                            "show # @",
                            "show names linked group",
                            "show number linked group",
                            "show number linked all"]
        self.help_hash = ["hash #",
                            "hash me (numbers)",
                            "hash (numbers) @ (numbers)",
                            "hash contact (numbers)",
                            "hash contacts (numbers)"]
        self.help_services = ["push services",
                            "push services (number)",
                            "gem services",
                            "gem services (number)",
                            "bot services",
                            "bot services (number)"]
        self.help_info = ["mid",
                            "gid",
                            "gcreator",
                            "gpic",
                            "date created"]
        self.help_owner = ["help normal",
                            "time left",
                            "cancelall",
                            "set message string",
                            "last seen name",
                            "show groups",
                            "show group members (number)",
                            "leave group number(s)",
                            "show names linked all",
                            "accept invites",
                            "announcement groupcast",
                            "secret groupcast",
                            "save last seen",
                            "add contact to push services",
                            "add contact to gem services",
                            "add contact to bot services"]
        self.push_services = [] #uid
        self.gem_services = [] #uid
        self.bot_services = [] #uid
        self.uids = [] #uid
        self.tags = [] #tag
        self.players = [] #tag
        self.aa_default = 3
        self.accounts_allowed = {} #uid:number
        self.last_seen = {} #uid:[gid,time,name]
        self.contacts = {} #uid:[gid,reason,number] if number==0, thats means unlimited
                            #some reasons will have 4 elements in the list

### CHAT COMMANDS ###

    #returns a string
    def normaliseHash(self,raw_hash):
        player_hash = raw_hash.upper()
        if player_hash.find(" ") != -1:
            space = player_hash.find(" ")
            player_hash = player_hash[:space]
        player_hash = player_hash.replace("0","O").replace("1","I")
        return player_hash

    #returns a list of numbers in ascending order
    def numberTextToList(self,text):
        numbertext = ""
        i = 0
        while i < len(text):
            try:
                numbertext += str(int(text[i]))
            except ValueError:
                numbertext += " "
            i += 1
        nlist = numbertext.split()
        numbers = [int(n) for n in nlist]
        set_num = set(numbers)
        if 0 in set_num:
            set_num.remove(0)
        numbers = list(set_num)
        numbers.sort()
        return numbers

    #returns a string
    def mainHelpMessage(self,sender, owner_name):
        #create help menu
        string = "##HELP##\n(Brackets are optional)\n"
        #add basic menu
        for b in self.help_base:
            string += "\n%s" % b
        string += "\n"
        for m in self.help_misc:
            string += "\n%s%s" % (self.rname, m)
        string += "\n"
        for l in self.help_link:
            string += "\n%s%s" % (self.rname, l)
        string += "\n"
        for s in self.help_show:
            string += "\n%s%s" % (self.rname, s)
        string += "\n"
        for h in self.help_hash:
            string += "\n%s%s" % (self.rname, h)
        string += "\n"
        for s in self.help_services:
            string += "\n%s%s" % (self.rname, s)
        for i in self.help_info:
            string += "\n%s%s" % (self.rname, i)
        string += "\n"
        #add owner help if owner
        if sender == self.owner:
            for o in self.help_owner:
                string += "\n%s%s" % (self.rname, o)
        else:
            string += "\n If the bot is not working, check it's status message. For more info, message %s." % owner_name
        return string

    #returns a string
    def timeToSeasonEndMessage(self, end_time):
        end = end_time
        now = time.time()
        time_left = end-now
        if time_left < 60:
            return "Season has ended."
        else:
            m, s = divmod(time_left, 60)
            h, m = divmod(m, 60)
            d, h = divmod(h, 24)
            if d == 0:
                if h == 0:
                    string = "Season ends in: %dm." % m
                else:
                    string = "Season ends in: %dh %dm." % (h,m)
            else:
                string = "Season ends in: %dd %dh." % (d,h)
            return string

    #returns a string
    def linkToTag(self, raw_hash,mid):
        n_accounts = self.uids.count(mid) #number of accounts linked
        if mid in self.accounts_allowed.keys():
            aa = self.accounts_allowed[mid]
        else:
            aa = self.aa_default
        #aa is accounts allowed
        if n_accounts < aa:
            player_hash = self.normaliseHash(raw_hash)
            if player_hash in self.tags:
                return "Someone is already linked to this #."
            else:
                player = g_coc.player_info(player_hash)
                if g_coc.statusCode == 200:
                    query = "INSERT INTO `linkedPlayers` (`uid`,`tag`) VALUES ('%s','%s')" % (mid, player_hash)
                    cur.execute(query)
                    self.uids.append(mid)
                    self.tags.append(player_hash)
                    if player_hash not in self.players:
                        query = "INSERT INTO `players` (`tag`) VALUES ('%s')" % player_hash
                        cur.execute(query)
                        self.players.append(player_hash)
                    return "You have been linked to %s (%s/%s)." % (player_hash,n_accounts+1,aa)
                elif g_coc.statusCode == 404:
                    return "%s is not a valid #." % player_hash
                else:
                    return g_coc.statusReasons[g_coc.statusCode]
        else:
            return "You are already linked to your maximum number of #s allowed.\n(%s)" % aa

    #returns a string
    def unlinkFromTagByNumber(self, number_list,mid):
        if mid in self.uids:
            n_accounts = self.uids.count(mid)
            allowed_numbers = [nl for nl in number_list if nl <= n_accounts]
            if len(allowed_numbers) == 0:
                return "You must include at least one number that corresponds to a # you are linked to."
            else:
                uid_indexes = [i for i in range(len(self.uids)) if self.uids[i] == mid]
                tag_indexes = [uid_indexes[an-1] for an in allowed_numbers]
                tag_indexes.reverse() #because itll get shorter
                unlinked_tags = []
                for ti in tag_indexes:
                    unlinked_tags.append(self.tags[ti])
                    query = "DELETE FROM linkedPlayers WHERE tag = '%s'" % self.tags[ti]
                    cur.execute(query)
                    del self.tags[ti]
                    del self.uids[ti]
                string = "You have been unlinked from:"
                for ut in unlinked_tags:
                    string += "\n%s" % ut
                return string
        else:
            return "You are not linked to a #."

    #returns a string
    def unlinkFromTagByTag(self, tag,mid):
        if mid in self.uids:
            if tag in self.tags:
                index = self.tags.index(tag)
                if self.uids[index] == mid:
                    query = "DELETE FROM linkedPlayers WHERE tag = '%s'" % tag
                    cur.execute(query)
                    del self.uids[index]
                    del self.tags[index]
                    return "You have been unlinked from %s." % tag
                else:
                    return "You are not linked to this tag."
            else:
                return "You are not linked to this tag."
        else:
            return "You are not linked to a #."

    #returns a list of tags
    def showTagsListOfUid(self,mid):
        tags = [self.tags[i] for i in range(len(self.uids)) if self.uids[i] == mid]
        return tags

    #returns a list of messages
    def makeAndSplitListMessage(self,start,mlist): 
        if (len(start) > 2000) or (len(max(mlist, key=len)) > 2000):
            return ["Argument is too long."]
        else:
            messages = []
            string = start
            length = 0
            i = 0
            while i < len(mlist):
                if len(string+mlist[i]) > 2000:
                    messages.append(string)
                    string = mlist[i]
                else:
                    string += mlist[i]
                i += 1
            messages.append(string)
            return messages

    #returns string ok or problem
    def addToService(self,service,mid):
        try:
            services = ["coc-push",
                        "coc-gem",
                        "coc-bot"]
            if service == "coc-push":
                if mid in self.push_services:
                    return "Already in push services."
                else:
                    query = "INSERT INTO `services` (`type`,`uid`) VALUES ('%s','%s')" % (service,mid)
                    cur.execute(query)
                    self.push_services.append(mid)
                    return "Added to push services."
            elif service == "coc-gem":
                if mid in self.gem_services:
                    return "Already in gem services."
                else:
                    query = "INSERT INTO `services` (`type`,`uid`) VALUES ('%s','%s')" % (service,mid)
                    cur.execute(query)
                    self.gem_services.append(mid)
                    return "Added to gem services."
            elif service == "coc-bot":
                if mid in self.bot_services:
                    return "Already in bot services."
                else:
                    query = "INSERT INTO `services` (`type`,`uid`) VALUES ('%s','%s')" % (service,mid)
                    cur.execute(query)
                    self.bot_services.append(mid)
                    return "Added to bot services."
            else:
                return "Invalid service."
        except Exception as e:
            print e
            return "Error"


### NON CHAT COMMANDS - FOR UPDATING TABLES###

    def pullLinkedPlayers(self):
        try:
            self.uids = []
            self.tags = []
            cur.execute("SELECT * FROM linkedPlayers")
            for row in cur.fetchall():
                self.uids.append(row[0]) #uid
                self.tags.append(row[1]) #tag
            return "ok"
        except Exception as e:
            return e

    def pullPlayers(self):
        try:
            self.players = []
            cur.execute("SELECT * FROM players")
            for row in cur.fetchall():
                self.players.append(row[0]) #uid
            return "ok"
        except Exception as e:
            return e

    def pullAccountsAllowed(self):
        try:
            self.accounts_allowed = {}
            cur.execute("SELECT * FROM accountsAllowed")
            for row in cur.fetchall():
                self.accounts_allowed[row[0]] = int(row[1]) # uid:number
            return "ok"
        except Exception as e:
            return e

    def pullAllNecessary(self):
        response = []
        response.append(self.pullLinkedPlayers())
        response.append(self.pullPlayers())
        response.append(self.pullAccountsAllowed())
        response.append(self.pullServices())
        response.append(self.pullLastSeen())
        result = ""
        #check whether any errors
        for r in response:
            result = r
            if r != "ok":
                break
        return result

    def saveLastSeen(self):
        try:
            cur.execute("TRUNCATE TABLE lastSeen")
            for uid in self.last_seen.keys():
                query = 'INSERT INTO `lastSeen` (`uid`,`gid`,`time`,`name`) VALUES ("%s","%s","%s","%s")'
                tlist = [uid, self.last_seen[uid][0], self.last_seen[uid][1], self.last_seen[uid][2]]
                tup = tuple(tlist)
                cur.execute(query, tup)
            return "ok"
        except Exception as e:
            return e

    def pullLastSeen(self):
        try:
            self.last_seen = {}
            cur.execute("SELECT * FROM lastSeen")
            for row in cur.fetchall():
                self.last_seen[row[0]] = [row[1],row[2],row[3]]
            return "ok"
        except Exception as e:
            return e

    def enforceAaChanges(self):
        try:
            mids = self.accounts_allowed.keys()
            for mid in mids:
                uid_indexes = [i for i in range(len(self.uids)) if self.uids[i] == mid]
                extra = len(uid_indexes) - self.accounts_allowed[mid]
                while extra > 0:
                    tag = self.tags[uid_indexes[-1]]
                    del self.uids[uid_indexes[-1]]
                    del self.tags[uid_indexes[-1]]
                    query = "DELETE FROM linkedPlayers WHERE tag = '%s'" % tag
                    cur.execute(query)
                    extra = extra -1
            return "ok"
        except Exception as e:
            return e

    def removeDefaultAa(self):
        try:
            query = "DELETE FROM accountsAllowed WHERE number = '%s'" % self.aa_default
            cur.execute(query)
            aa_keys = self.accounts_allowed.keys()
            for ak in aa_keys:
                aa = self.accounts_allowed[ak]
                if aa == self.aa_default:
                    del self.accounts_allowed[ak]
            return "ok"
        except Exception as e:
            return e

    def pullServices(self):
        try:
            services = [] #servicetype, uid
            query = "SELECT * FROM services"
            cur.execute(query)
            for row in cur.fetchall():
                services.append([row[0],row[1]])
            for s in services:
                if s[0] == "coc-push":
                    self.push_services.append(s[1])
                elif s[0] == "coc-gem":
                    self.gem_services.append(s[1])
                elif s[0] == "coc-bot":
                    self.bot_services.append(s[1])
            return "ok"
        except Exception as e:
            return e

    def checkUpdateToken(token,self):
        cur.execute("SELECT * FROM token")
        tokens = []
        for row in cur.fetchall():
            tokens.append(row[0])
        if len(tokens) == 0:
            query = 'INSERT INTO `token` (`token`,`time`) VALUES ("%s", "%s")' % (token,time.time())
            cur.execute(query)
            print "Token added to database."
        else:
            last_token = tokens[0]
            if last_token != token:
                cur.execute("TRUNCATE TABLE token")
                query = 'INSERT INTO `token` (`token`,`time`) VALUES ("%s", "%s")' % (token,time.time())
                cur.execute(query)
                print "Token updated"
            else:
                print "Token unchanged."

    def tokenTimeMade(self):
        cur.execute("SELECT * FROM token")
        times = []
        for row in cur.fetchall():
            times.append(row[1])
        t = times[0]
        t = float(t)
        return int(t)
