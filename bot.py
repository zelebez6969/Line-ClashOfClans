# -*- coding: utf-8 -*-
from Liberation import LineClient
from Liberation.Api import LineTracer
from Liberation.LineThrift.ttypes import Message, TalkException
from thrift.Thrift import TType, TMessageType, TException, TApplicationException
from Liberation.LineThrift.TalkService import Client
from multiprocessing import Process
from commands import commands
import sys, os, time, atexit, random, ast
from main_profile import cocapi
from datetime import datetime
#=================================================
reload(sys)
sys.setdefaultencoding('utf-8')
#=================================================
#NOTE mid and uid are used interchangably

do = commands()
g_coc = cocapi()

#Pull all data from tables
setup = []
setup.append(do.pullAllNecessary())
setup.append(do.enforceAaChanges())
setup.append(do.removeDefaultAa())
for s in setup:
    if s != "ok":
        raise Exception(s)
print "Setup Complete."
#==================================================

##LOGIN##
token = "token"
client = LineClient()
client._tokenLogin(token)

profile, setting, tracer = client.getProfile(), client.getSettings(), LineTracer(client)
offbot, messageReq, wordsArray, waitingAnswer = [], {}, {}, {}

print client._loginresult()

do.checkUpdateToken(token)

### IMPORTANT FUNCTIONS ###

def sendMessage(to, text, contentMetadata={}, contentType=0):
    mes = Message()
    mes.to, mes.from_ = to, profile.mid
    mes.text = text

    mes.contentType, mes.contentMetadata = contentType, contentMetadata
    if to not in messageReq:
        messageReq[to] = -1
    messageReq[to] += 1
    client._client.sendMessage(messageReq[to], mes)

def makeSendMainProfile(player_hash, to):
    name = str(random.randint(10000,99999))
    path = ""
    response = g_coc.makeProfile(player_hash, name=name, path=path)
    if response == 200:
        client.sendImage(to_=to, path=(name+".jpg"))
        os.remove(name+".jpg")
    elif response == 404:
        sendMessage(to=to, text="%s is not a valid #." % player_hash)
    else:
        sendMessage(to=to, text=g_coc.statusReasons[response])

def exitHandler():
    do.saveLastSeen()
atexit.register(exitHandler)

### MAIN BOT OPERATIONS ###

def NOTIFIED_ADD_CONTACT(op):
    client.findAndAddContactsByMid(op.param1)
    sendMessage(to=do.owner, text=(client.getContact(op.param1).displayName+" added you as a friend."))
    sendMessage(to=do.owner, text="", contentMetadata={"mid":op.param1}, contentType=13)
    name = client.getContact(op.param1).displayName
    do.last_seen[op.param1] = ["add contact", time.time(), name]
tracer.addOpInterrupt(5, NOTIFIED_ADD_CONTACT)

def NOTIFIED_INVITE_INTO_GROUP(op):
    if profile.mid in op.param3:
        try:
            client.acceptGroupInvitation(op.param1)
            string = "Thanks for inviting me. I cannot kick invite, or change group settings. For more information, type '%shelp'. To make me leave, type '%s@bye'." % (do.rname,do.rname)
            string += "\nType '%sIMPORTANT' if you haven't seen it before." % do.rname
            sendMessage(to=op.param1, text=string)
        except Exception as e:
            print e
    name = client.getContact(op.param2).displayName
    do.last_seen[op.param2] = [op.param1, time.time(), name]
tracer.addOpInterrupt(13, NOTIFIED_INVITE_INTO_GROUP)

def NOTIFIED_INVITE_INTO_ROOM(op):
    sendMessage(to=msg.to, text="Sorry, I don't work in rooms.")
    client.leaveRoom(op.param1)
    name = client.getContact(op.param2).displayName
    do.last_seen[op.param2] = ["room", time.time(), name]
tracer.addOpInterrupt(22, NOTIFIED_INVITE_INTO_ROOM)

def NOTIFIED_READ_MESSAGE(op):
    name = client.getContact(op.param2).displayName
    do.last_seen[op.param2] = [op.param1, time.time(), name]
tracer.addOpInterrupt(55, NOTIFIED_READ_MESSAGE)

def RECEIVE_MESSAGE(op):
    msg = op.message
    if msg.contentType == 0:
        try:
            text = msg.text.rstrip()
            if msg.toType == 0:
                msg.to = msg.from_
            if text.lower() == "help":
                sendMessage(to=msg.to, text="Type '%shelp' for a detailed help list." % do.rname)
            elif text.lower() in ["rname","responsename"]:
                sendMessage(to=msg.to, text=do.rname)
            elif text[:len(do.rname)] == do.rname:
                if msg.from_ == "u5d5b406851db8c08a7107ca9b0d68d52":
                    sendMessage(to=msg.to, text="Hey, guys! I found waldo :)!!")
                text = text[len(do.rname):]
                if text.lower() == "season end":
                    se = do.timeToSeasonEndMessage(do.season_end)
                    sendMessage(to=msg.to, text=se)
                elif text.lower() == "help":
                    name = client.getContact(do.owner).displayName
                    mhm = do.mainHelpMessage(msg.from_, name)
                    sendMessage(to=msg.to, text=mhm)
                elif text.lower() == "@bye":
                    client.leaveGroup(msg.to)
                elif text.lower() == "important":
                    string = "".join(do.letter_sealing_list)
                    sendMessage(to=msg.to, text=string)
                elif text.lower() == "mid":
                    sendMessage(to=msg.to, text=msg.from_)
                elif text.lower() == "gid":
                    sendMessage(to=msg.to, text=msg.to)
                elif text.lower() == "gcreator":
                    try:
                        mid = group.creator.mid
                        sendMessage(to=msg.to, text="", contentMetadata={"mid":mid}, contentType=13)
                    except:
                        sendMessage(to=msg.to, text="No creator.")
                elif text.lower() == "gpic":
                    picture_url = "http://dl.profile.line.naver.jp/"
                    group = client.getGroup(msg.to)
                    picture_url += group.pictureStatus
                    client.sendImageWithURL(to_=msg.to, url=picture_url)
                elif text.lower() == "date created":
                    group = client.getGroup(msg.to)
                    t = group.createdTime
                    string = datetime.fromtimestamp(t).strftime("%A, %B %d, %Y %I:%M:%S")
                    sendMessage(to=msg.to, text=string)
                elif text.lower() == "tag contact":
                    do.contacts[msg.from_] = [msg.to,"tag",1]
                    sendMessage(to=msg.to, text="Send a contact.")
                elif text.lower() == "tag contacts":
                    do.contacts[msg.from_] = [msg.to,"tag",0]
                    sendMessage(to=msg.to, text="Send contacts.")
                elif text.lower() == "message":
                    string = do.set_message
                    sendMessage(to=msg.to, text=string)
                elif text[:12].lower() == "link me to #":
                    raw_hash = text[11:]
                    ltt = do.linkToTag(raw_hash,msg.from_)
                    sendMessage(to=msg.to,text=ltt)
                elif text.lower() == "unlink me":
                    #unlink from last tag
                    tags = do.showTagsListOfUid(msg.from_)
                    if len(tags) == 0:
                        sendMessage(to=msg.to,text="You are not linked to a #.")
                    else:
                        number_list = [len(tags)]
                        uftbn = do.unlinkFromTagByNumber(number_list,msg.from_)
                        sendMessage(to=msg.to, text=uftbn)
                elif text.lower() == "unlink me from all":
                    tags = do.showTagsListOfUid(msg.from_)
                    if len(tags) == 0:
                        sendMessage(to=msg.to,text="You are not linked to a #.")
                    else:
                        numbers = range(1,len(tags)+1)
                        uftbn = do.unlinkFromTagByNumber(numbers,msg.from_)
                        sendMessage(to=msg.to, text=uftbn)
                elif text[:16].lower() == "unlink me from #":
                    raw_hash = text[15:]
                    player_hash = do.normaliseHash(raw_hash)
                    uftbt = do.unlinkFromTagByTag(player_hash,msg.from_)
                    sendMessage(to=msg.to, text=uftbt)
                elif text[:14].lower() == "unlink me from":
                    numbertext = text[14:]
                    nlist = do.numberTextToList(numbertext)
                    uftbn = do.unlinkFromTagByNumber(nlist,msg.from_)
                    sendMessage(to=msg.to, text=uftbn)
                elif text.lower() in ["show my #","show my #s"]:
                    if msg.from_ in do.accounts_allowed.keys():
                        aa = do.accounts_allowed[mid]
                    else:
                        aa = do.aa_default
                    tags = do.showTagsListOfUid(msg.from_)
                    if len(tags) == 0:
                        string = "You are not linked to a #. (0/%s)" % aa
                    else:
                        string = "You are linked to:"
                        i = 0
                        while i < len(tags):
                            string += "\n%s. %s" % (i+1,tags[i])
                            i += 1
                        string += "\n(%s/%s)" % (len(tags),aa)
                    sendMessage(to=msg.to, text=string)
                elif text[:17].lower() == "show contact of #":
                    raw_hash = text[16:]
                    player_hash = do.normaliseHash(raw_hash)
                    if player_hash in do.tags:
                        tag_index = do.tags.index(player_hash)
                        uid = do.uids[tag_index]
                        sendMessage(to=msg.to, text="", contentMetadata={"mid":uid}, contentType=13)
                    else:
                        sendMessage(to=msg.to, text="No one is linked to %s." % player_hash)
                elif text.lower() == "show # of contact": #reason = "show #"
                    do.contacts[msg.from_] = [msg.to,"show #",1]
                    sendMessage(to=msg.to, text="Send a contact.")
                elif text.lower() == "show # of contacts": #reason = "show #"
                    do.contacts[msg.from_] = [msg.to,"show #",0]
                    sendMessage(to=msg.to, text="Send contacts.")
                elif text.lower() == "show names linked group":
                    group = client.getGroup(msg.to)
                    gnames = [contact.displayName for contact in group.members]
                    gmids = [contact.mid for contact in group.members]
                    #nal is number of accounts linked
                    nal = [do.uids.count(gmid) for gmid in gmids if gmid in do.uids]
                    #lnames is linked names
                    lnames = [gnames[i] for i in range(len(gnames)) if gmids[i] in do.uids]
                    mlist = ["\n%s (%s)" % (lnames[i],nal[i]) for i in range(len(nal))]
                    if len(mlist) == 0:
                        sendMessage(to=msg.to, text="No one here is linked to a #.")
                    else:
                        start_message = "Linked players in %s:\n" % group.name
                        start_message += "\n%s people total\n" % len(mlist)
                        messages = do.makeAndSplitListMessage(start_message,mlist)
                        for m in messages:
                            sendMessage(to=msg.to, text=m)
                elif text.lower() == "show number linked group":
                    group = client.getGroup(msg.to)
                    gnames = [contact.displayName for contact in group.members]
                    gmids = [contact.mid for contact in group.members]
                    linked_mids = [gmid for gmid in gmids if gmid in do.uids]
                    luids = len(linked_mids)
                    ltags = 0
                    for lm in linked_mids:
                        c = do.showTagsListOfUid(lm)
                        ltags += len(c)
                    sendMessage(to=msg.to, text="%s people are linked to %s tags in this group." % (luids, ltags))
                elif text.lower() == "show number linked all":
                    luids = len(set(do.uids))
                    ltags = len(do.tags)
                    sendMessage(to=msg.to, text="%s people are linked to %s tags overall." % (luids, ltags))
                elif text[:6].lower() == "hash #":
                    player_hash = do.normaliseHash(text[5:])
                    Process(target=makeSendMainProfile, args=(player_hash,msg.to)).start()
                elif text.lower() == "hash me":
                    tags = do.showTagsListOfUid(msg.from_)
                    if len(tags) == 0:
                        sendMessage(to=msg.to, text="You are not linked to a #.")
                    else:
                        tag = tags[0]
                        Process(target=makeSendMainProfile, args=(tag,msg.to)).start()
                elif text[:7].lower() == "hash me":
                    numbertext = text[7:]
                    numbers = do.numberTextToList(numbertext)
                    tags = do.showTagsListOfUid(msg.from_)
                    if len(numbers) == 0:
                        sendMessage(to=msg.to, text="You have not included any numbers.")
                    elif len(tags) == 0:
                        sendMessage(to=msg.to, text="You are not linked to a #.")
                    else:
                        use_tags = [tags[i-1] for i in numbers if i <= len(tags)]
                        if len(use_tags) == 0:
                            sendMessage(to=msg.to, text="You have not included any numbers that correspond to a # linked to your account.")
                        else:
                            for ut in use_tags:
                                Process(target=makeSendMainProfile, args=(ut,msg.to)).start()
                elif text.lower() == "hash contact": #reason = "image main_profile"
                    do.contacts[msg.from_] = [msg.to,"image main_profile",1,[1]]
                    #4th element is which tag(s), starting from 1
                    sendMessage(to=msg.to, text="Send a contact.")
                elif text[:12].lower() == "hash contact": #reason = "image main_profile"
                    numbertext = text[12:]
                    #4th element is which tag(s), starting from 1
                    nlist = do.numberTextToList(numbertext)
                    if len(nlist) == 0:
                        nlist = [1]
                    do.contacts[msg.from_] = [msg.to,"image main_profile",1,nlist]
                    sendMessage(to=msg.to, text="Send a contact.")
                elif text.lower() == "hash contacts": #reason = "image main_profile"
                    do.contacts[msg.from_] = [msg.to,"image main_profile",0,[1]]
                    sendMessage(to=msg.to, text="Send contacts.")
                elif text[:13].lower() == "hash contacts": #reason = "image main_profile"
                    numbertext = text[13:]
                    nlist = do.numberTextToList(numbertext)
                    if len(nlist) == 0:
                        nlist = [1]
                    do.contacts[msg.from_] = [msg.to,"image main_profile",0,nlist]
                    sendMessage(to=msg.to, text="Send contacts.")
                elif text.lower() == "contacts off":
                    if msg.from_ in do.contacts.keys():
                        del do.contacts[msg.from_]
                        sendMessage(to=msg.to, text="Action by contact has been turned off.")
                    else:
                        sendMessage(to=msg.to, text="You do not have action by contact on.")
                elif text.lower() == "push services":
                    if len(do.push_services) == 0:
                        string = "No one is currently advertising push services here."
                    else:
                        string = "People offering push services:\n"
                        i = 0
                        while i < len(do.push_services):
                            name = client.getContact(do.push_services[i]).displayName
                            string += "\n%s. %s" % (i+1,name)
                            i += 1
                        string += "\n\nSend '%spush services number for a person's contact." % do.rname
                        string += "\nYou can pm the person, however they also usually have a group you can join."
                    sendMessage(to=msg.to, text=string)
                elif text[:13].lower() == "push services":
                    numbertext = text[13:]
                    numbers = do.numberTextToList(numbertext)
                    if len(numbers) == 0:
                        sendMessage(to=msg.to, text="You did not include a number.")
                    else:
                        allowed_indexes = [n-1 for n in numbers if n <= len(do.push_services)]
                        if len(allowed_indexes) == 0:
                            sendMessage(to=msg.to, text="You did not send a number from the list.")
                        else:
                            mids = [do.push_services[ai] for ai in allowed_indexes]
                            for mid in mids:
                                sendMessage(to=msg.to, text="", contentMetadata={"mid":mid}, contentType=13)
                elif text.lower() == "gem services":
                    if len(do.gem_services) == 0:
                        string = "No one is currently advertising gem services here."
                    else:
                        string = "People offering gem services:\n"
                        i = 0
                        while i < len(do.gem_services):
                            name = client.getContact(do.gem_services[i]).displayName
                            string += "\n%s. %s" % (i+1,name)
                            i += 1
                        string += "\n\nSend '%sgem services number for a person's contact." % do.rname
                        string += "\nYou can pm the person, however they also usually have a group you can join."
                    sendMessage(to=msg.to, text=string)
                elif text[:12].lower() == "gem services":
                    numbertext = text[12:]
                    numbers = do.numberTextToList(numbertext)
                    if len(numbers) == 0:
                        sendMessage(to=msg.to, text="You did not include a number.")
                    else:
                        allowed_indexes = [n-1 for n in numbers if n <= len(do.gem_services)]
                        if len(allowed_indexes) == 0:
                            sendMessage(to=msg.to, text="You did not send a number from the list.")
                        else:
                            mids = [do.gem_services[ai] for ai in allowed_indexes]
                            for mid in mids:
                                sendMessage(to=msg.to, text="", contentMetadata={"mid":mid}, contentType=13)
                elif text.lower() == "bot services":
                    if len(do.bot_services) == 0:
                        string = "No one is currently advertising bot services here."
                    else:
                        string = "People offering bot services:\n"
                        i = 0
                        while i < len(do.bot_services):
                            name = client.getContact(do.bot_services[i]).displayName
                            string += "\n%s. %s" % (i+1,name)
                            i += 1
                        string += "\n\nSend '%sbot services number for a person's contact." % do.rname
                        string += "\nYou can pm the person, however they also usually have a group you can join."
                    sendMessage(to=msg.to, text=string)
                elif text[:12].lower() == "bot services":
                    numbertext = text[12:]
                    numbers = do.numberTextToList(numbertext)
                    if len(numbers) == 0:
                        sendMessage(to=msg.to, text="You did not include a number.")
                    else:
                        allowed_indexes = [n-1 for n in numbers if n <= len(do.bot_services)]
                        if len(allowed_indexes) == 0:
                            sendMessage(to=msg.to, text="You did not send a number from the list.")
                        else:
                            mids = [do.bot_services[ai] for ai in allowed_indexes]
                            for mid in mids:
                                sendMessage(to=msg.to, text="", contentMetadata={"mid":mid}, contentType=13)
                elif len(msg.contentMetadata) != 0:
                    mentions = ast.literal_eval(msg.contentMetadata["MENTION"])
                    mids = [m["M"] for m in mentions["MENTIONEES"]]
                    starts = [(int(m["S"])-len(do.rname)) for m in mentions["MENTIONEES"]]
                    ends = [(int(m["E"])-len(do.rname)) for m in mentions["MENTIONEES"]]
                    if text[:11].lower() == "show # of @":
                        for mid in mids:
                            uid_indexes = [i for i in range(len(do.uids)) if do.uids[i]==mid]
                            tags = [do.tags[ui] for ui in uid_indexes]
                            name = client.getContact(mid).displayName
                            string = "%s:" % name
                            for i in range(len(tags)):
                                string += "\n%s. %s" % (i+1,tags[i])
                            if len(tags) == 0:
                                string ="%s is not linked to a #." % name
                            sendMessage(to=msg.to, text=string)
                    elif text[:5].lower() == "hash ":
                        numbertext = text[5:starts[0]]
                        numbers = do.numberTextToList(numbertext)
                        if len(numbers) == 0:
                            #add extra to make sure u get stuff at the end
                            text += " hmm"
                            not_linked = []
                            for i in range(len(mids)-1):
                                mid = mids[i]
                                if mid in do.uids:
                                    end = ends[i]
                                    start = starts[i+1]
                                    numbertext = text[end:start]
                                    numbers = do.numberTextToList(numbertext)
                                    if len(numbers) == 0:
                                        numbers = [1]
                                    uid_indexes = [i for i in range(len(do.uids)) if do.uids[i]==mid]
                                    tags = [do.tags[ui] for ui in uid_indexes]
                                    r_tags = [tags[n-1] for n in numbers if n <= len(tags)]
                                    if len(r_tags) == 0:
                                        not_linked.append(mid)
                                    else:
                                        for rt in r_tags:
                                            Process(target=makeSendMainProfile, args=(rt,msg.to)).start()
                                else:
                                    not_linked.append(mid)
                            mid = mids[-1]
                            if mid in do.uids:
                                end = ends[-1]
                                start = len(text)-1
                                numbertext = text[end:start]
                                numbers = do.numberTextToList(numbertext)
                                if len(numbers) == 0:
                                    numbers = [1]
                                uid_indexes = [i for i in range(len(do.uids)) if do.uids[i]==mid]
                                tags = [do.tags[ui] for ui in uid_indexes]
                                r_tags = [tags[n-1] for n in numbers if n <= len(tags)]
                                if len(r_tags) == 0:
                                    not_linked.append(mid)
                                else:
                                    for rt in r_tags:
                                        Process(target=makeSendMainProfile, args=(rt,msg.to)).start()
                            else:
                                not_linked.append(mid)
                            if len(not_linked) != 0:
                                string = "Not linked to specified number of tags:\n"
                                for nl in not_linked:
                                    name = client.getContact(nl).displayName
                                    string += "\n%s" % name
                                sendMessage(to=msg.to, text=string)
                        else:
                            #check if numbers are allowed and then hash them
                            not_linked = [] #uids
                            for i in range(len(mids)):
                                mid = mids[i]
                                if mid in do.uids:
                                    uid_indexes = [i for i in range(len(do.uids)) if do.uids[i]==mid]
                                    tags = [do.tags[ui] for ui in uid_indexes]
                                    r_tags = [tags[n-1] for n in numbers if n <= len(tags)]
                                    if len(r_tags) == 0:
                                        not_linked.append(mid)
                                    else:
                                        for rt in r_tags:
                                            Process(target=makeSendMainProfile, args=(rt,msg.to)).start()
                                else:
                                    not_linked.append(mid)
                            if len(not_linked) != 0:
                                string = "Not linked to specified number of tags:\n"
                                for nl in not_linked:
                                    name = client.getContact(nl).displayName
                                    string += "\n%s" % name
                                sendMessage(to=msg.to, text=string)
                elif msg.from_ == do.owner:
                    if text.lower() == "help normal":
                        name = client.getContact(do.owner).displayName
                        mhm = do.mainHelpMessage("normal mid", name)
                        sendMessage(to=msg.to, text=mhm)
                    elif text.lower()== "time left":
                        t = do.tokenTimeMade()
                        expires = t + (24*60*60)
                        now = time.time()
                        change = int(expires - now)
                        if change > 0:
                            m, s = divmod(change, 60)
                            h, m = divmod(m, 60)
                            d, h = divmod(h, 24)
                            string = "%sd %sh %sm %ss." % (d,h,m,s)
                            sendMessage(to=msg.to, text=string)
                        else:
                            sendMessage(to=msg.to, text="Expired.")
                    elif text.lower() == "cancelall":
                        group = client.getGroup(msg.to)
                        invites = [contact.mid for contact in group.invitee]
                        ps = []
                        for i in invites:
                            ps.append(Process(target=client.cancelGroupInvitation, args=(msg.to,[i])))
                        for p in ps:
                            p.start()
                    elif text[:11].lower() == "set message":
                        message = text[11:]
                        do.set_message = message
                        sendMessage(to=msg.to, text="Message updated.")
                    elif text.lower() == "show groups":
                        gids = client.getGroupIdsJoined()
                        working_groups = []
                        for gid in gids:
                            try:
                                group = client.getGroup(gid)
                                working_groups.append(group)
                            except:
                                pass
                        string = "Groups Joined:\n(%s)\n" % len(working_groups)
                        i = 0
                        while i < len(working_groups):
                            group = working_groups[i]
                            name = group.name
                            size = len(group.members)
                            string += "\n%s. %s [%s]" % (i+1,name,size)
                            i += 1
                        sendMessage(to=msg.to, text=string)
                    elif text[:18].lower() == "show group members":
                        #uses the first valid number
                        numbertext = text[18:]
                        numbers = do.numberTextToList(numbertext)
                        gids = client.getGroupIdsJoined()
                        working_gids = []
                        for gid in gids:
                            try:
                                gname = client.getGroup(gid).name
                                working_gids.append(gid)
                            except:
                                pass
                        allowed_indexes = [n-1 for n in numbers if n <= len(working_gids)]
                        if len(allowed_indexes) == 0:
                            sendMessage(to=msg.to, text="You did not provide a valid number.")
                        else:
                            index = allowed_indexes[0]
                            gid = working_gids[index]
                            group = client.getGroup(gid)
                            gname = group.name
                            member_names = [contact.displayName for contact in group.members]
                            string = "%s members:\n(%s)\n" % (gname,len(member_names))
                            for mn in member_names:
                                string += "\n%s" % mn
                            sendMessage(to=msg.to, text=string)
                    elif text[:11].lower() == "leave group":
                        numbertext = text[11:]
                        numbers = do.numberTextToList(numbertext)
                        gids = client.getGroupIdsJoined()
                        working_gids = []
                        working_names = []
                        for gid in gids:
                            try:
                                group = client.getGroup(gid)
                                working_gids.append(gid)
                                working_names.append(group.name)
                            except:
                                pass
                        allowed_indexes = [n-1 for n in numbers if n <= len(working_gids)]
                        if len(allowed_indexes) == 0:
                            sendMessage(to=msg.to, text="You did not provide a valid number.")
                        else:
                            for ai in allowed_indexes:
                                try:
                                    client.leaveGroup(working_gids[ai])
                                    sendMessage(to=msg.to, text="Left %s." % working_names[ai])
                                except:
                                    sendMessage(to=msg.to, text="Failed to leave %s." % working_names[ai])
                    elif text.lower() == "show names linked all":
                        set_uids = set(do.uids)
                        names = [client.getContact(mid).displayName for mid in set_uids]
                        nal = [do.uids.count(mid) for mid in set_uids]
                        mlist = ["\n%s (%s)" % (names[i],nal[i]) for i in range(len(nal))]
                        start = "All linked players:\n"
                        start += "\n%s people total\n" % len(mlist)
                        messages = do.makeAndSplitListMessage(start,mlist)
                        for m in messages:
                            sendMessage(to=msg.to, text=m)
                    elif text.lower() == "accept invites":
                        gids = client.getGroupIdsInvited()
                        for gid in gids:
                            try:
                                client.acceptGroupInvitation(gid)
                                name = client.getGroup(gid).name
                                sendMessage(to=msg.to, text="Joined %s." % name)
                            except:
                                pass
                        sendMessage(to=msg.to, text="Done.")
                    elif text[:22].lower() == "announcement groupcast":
                        name = client.getContact(do.owner).displayName
                        message = text[22:].rstrip()
                        announcement = "Groupcast from %s:\n%s" % (name,message)
                        gids = client.getGroupIdsJoined()
                        for gid in gids:
                            try:
                                sendMessage(to=gid, text=announcement)
                            except:
                                pass
                    elif text[:16].lower() == "secret groupcast":
                        message = text[16:].rstrip()
                        gids = client.getGroupIdsJoined()
                        for gid in gids:
                            try:
                                sendMessage(to=gid, text=message)
                            except:
                                pass
                    elif text.lower() == "save last seen":
                        do.saveLastSeen()
                        sendMessage(to=msg.to, text="Done.")
                    elif text.lower() == "add contact to push services": #reason = "add to service"
                        do.contacts[msg.from_] = [msg.to,"add to service",1,"coc-push"]
                        sendMessage(to=msg.to, text="Send a contact.")
                    elif text.lower() == "add contact to gem services": #reason = "add to service"
                        do.contacts[msg.from_] = [msg.to,"add to service",1,"coc-gem"]
                        sendMessage(to=msg.to, text="Send a contact.")
                    elif text.lower() == "add contact to bot services": #reason = "add to service"
                        do.contacts[msg.from_] = [msg.to,"add to service",1,"coc-bot"]
                        sendMessage(to=msg.to, text="Send a contact.")
        except Exception as e:
            print e
    elif msg.contentType == 13:
        try:
            if msg.from_ in do.contacts.keys():
                if do.contacts[msg.from_][0] == msg.to:
                    mid = msg.contentMetadata["mid"]
                    reason = do.contacts[msg.from_][1]
                    number = do.contacts[msg.from_][2]
                    if reason == "show #":
                        uid_indexes = [i for i in range(len(do.uids)) if do.uids[i]==mid]
                        tags = [do.tags[ui] for ui in uid_indexes]
                        name = client.getContact(mid).displayName
                        string = "%s:" % name
                        i = 0
                        while i < len(tags):
                            string += "\n%s. %s" % (i+1,tags[i])
                            i += 1
                        if len(string) == 0:
                            string = "%s contact is not linked to a #." % name
                        sendMessage(to=msg.to, text=string)
                    elif reason == "image main_profile":
                        numbers = do.contacts[msg.from_][3]
                        uid_indexes = [i for i in range(len(do.uids)) if do.uids[i]==mid]
                        tags = [do.tags[ui] for ui in uid_indexes]
                        r_tags = [tags[n-1] for n in numbers if n <= len(tags)]
                        if len(r_tags) == 0:
                            sendMessage(to=msg.to, text="None of the numbers correspond to a # linked to this contact's account.")
                        else:
                            for rt in r_tags:
                                Process(target=makeSendMainProfile, args=(rt,msg.to)).start()
                    elif reason == "add to service":
                        service = do.contacts[msg.from_][3]
                        ats = do.addToService(service,mid)
                        sendMessage(to=msg.to, text=ats)
                    elif reason == "tag":
                        mention = '{"MENTIONEES":[{"M":"%s","S":"0","E":"2"}]}' % mid
                        sendMessage(to=msg.to, text="@t", contentMetadata={"MENTION":mention})
                    if reason in ["show #",
                                    "image main_profile",
                                    "tag",
                                    "add to service"]:
                        if number == 1:
                            del do.contacts[msg.from_]
                        else:
                            do.contacts[msg.from_][2] = number-1
        except Exception as e:
            print op
            print e
    name = client.getContact(msg.from_).displayName
    do.last_seen[msg.from_] = [msg.to, time.time(), name]
tracer.addOpInterrupt(26, RECEIVE_MESSAGE)

while True:
    tracer.execute()
