import sys
import docopt
import re
import os
import csv
import sqlite3
from collections import *
from _kyodaishiki import _util
from _kyodaishiki import __data__
from _kyodaishiki import __shell__
from _kyodaishiki import __db__
from _kyodaishiki import __index__
from _kyodaishiki.shells import reference_book as rb
from . import util
from . import augment_hs
from . import mecab
from . import category
from . import select2
import copy
import _pyio
import subprocess as sp
import random
import shutil
import datetime
import crayons
import colorama
import winshell

ID_INDEX_DB_PATH="id_index.db"
ID_INDEX_TABLE_NAME="id_index_data"
KANA_TAG_TABLE_NAME="kana_tag_index_data"

def getCardFromID(indexcur,db,cardid):
    for indexstr in indexcur.execute(f"select indexstr from {ID_INDEX_TABLE_NAME} where cardid == '{cardid}'"):
        idx=__index__.Index.read(indexstr[0])
        card=db.get(idx)
        if card:
            yield card

def getIndexCards(indexdb,db,comment,depth=10**32):
    def tocard(card):
        tagIdxes=db.cardToTags.get(card.id)
        if not tagIdxes:
            return None
        return __index__.Card(card.memoIdx,card.commentIdx,tagIdxes,card.date)
    cur=indexdb.cursor()
    frontiers=deque([(comment,0)])
    explored=[]
    while frontiers:
        comment,cur_depth=frontiers.popleft()
        if cur_depth > depth:
            continue
        for cardid in map(int,re.findall("[\"\'#](?P<id>\d+)\.csm",comment)):
            #card=db.get(cardid)
            for card in getCardFromID(cur,db,cardid):
                if card.id in explored:
                    continue
                if card:
                    card=tocard(card)
                    yield card
                explored.append(card.id)
                frontiers.append((card.comment(db.text),cur_depth+1))

def createTableOfIdIndex(cur):
    cur.execute(f"create table if not exists {ID_INDEX_TABLE_NAME} (cardid int,indexstr text)")

def createIdIndex(sqldb,db):
    def append(cur,cardid,indexstr):
        cur.execute(f"insert into {ID_INDEX_TABLE_NAME} values (?,?)",(cardid,indexstr))
    cur=sqldb.cursor()
    createTableOfIdIndex(cur)
    for idIdx in db.cards:
        memo=idIdx.get(db.text)
        cardid=_util.hash(memo)
        append(cur,cardid,str(idIdx))
    sqldb.commit()

def createTableKanaOfTagIndex(cur):
    cur.execute(f"create table if not exists {KANA_TAG_TABLE_NAME} (kana str,tagidx text)")

def createKanaOfTagIndex(sqldb,db):
    def append(cur,tagIdx):
        tag=tagIdx.get(db.text)
        data=rb.convert(tag)
        cur.execute(f"insert into {KANA_TAG_TABLE_NAME} values (?,?)",(data["hira"],str(tagIdx)))
    cur=sqldb.cursor()
    createTableKanaOfTagIndex(cur)
    for tagIdx in db.tag.keys():
        append(cur,tagIdx)
    sqldb.commit()

def getTagFromKana(cur,db,kana):
    for data in cur.execute(f"select tagIdx from {KANA_TAG_TABLE_NAME} where kana like ?",[kana]):
        tagIdx=__index__.Index.read(data[0])
        tag=tagIdx.get(db.text)
        yield tag


class Attr(util.Attr):
	DBID="DBID"
	USERID="USERID"

class EnvKey:
	WRITE_TAGS="WRITETAGS"
	PORT="PORT"

class Docs:
	HELP="""
	Usage:
		help [(-a|--all)]
	"""
	SEARCH_CARD="""
	Usage:
                search_card index [(--dp <depth>)] [<searchArgs>...]
		search_card [(-t <tags>)] [(--nt <noTags>)] [(-m <memo>)] [(--mm <lowUpMemo>)] [(--em <escapedMemo>)] [(-c <comment>)] [(-a <all_text>)] [(-F <from>)] [(-U <until>)] [(-u <userid>)] [(-D <dbid>)] [(--pn|--printNot)]
	"""
	SEARCH="""
	Usage:
                search index (s|search) [(--dp <depth>)] [(-p <pMode>)] [<searchArgs>...] 
                search index [(--dp <depth>)] [(-t <tags>)] [(-m <memo>)] [(-p <pMode>)]
		search (n|not) [(-t <tags>)] [(--nt <noTags>)] [(-m <memo>)] [(--mm <lowUpMemo>)] [(--em <escapedMemo>)] [(-c <comment>)] [(-F <from>)] [(-U <until>)] [(-u <userid>)] [(-D <dbid>)] [(-p <pMode>)] [(-r|--random)] [(--al|--aslist)]
		search [(-t <tags>)] [(--nt <noTags>)] [(-m <memo>)] [(--mm <lowUpMemo>)] [(--em <escapedMemo>)] [(-c <comment>)] [(-a <all_text>)] [(-F <from>)] [(-U <until>)] [(-u <userid>)] [(-D <dbid>)] [(--pn|--printNot)] [(-p <pMode>)] [(-r|--random)]
	"""
	MAKE="""
	    Usage:
                make index id
                make index tag kana
                make index all
	"""
	GET="""
        Usage:
            get recent (s|search) [<searchArgs>...]
            get tag <kana>
            get <cardid> [(-p <pMode>)]
	"""
HELP="""
	help [(-a|--all)]
        search
        get
        make
"""

class Command(select2.Command):
    MAKE=("MA","MAKE")
    GET=("G","GET")

class DBShell(select2.DBShell):
	VIM_MAX=50
	VIM_COUNT_OF_FILE=50
	PROMPT=str(crayons.magenta(">>"))
	#PROMPT=">>"
	def indexdb(self):
            index_fname=os.path.join(self.db.dname,ID_INDEX_DB_PATH)
            return sqlite3.connect(index_fname)
	def execQuery(self,query,output=sys.stdout):
		if query.command in _util.Command.HELP:
			try:
				args=docopt.docopt(Docs.HELP,query.args)
			except SystemExit:
				return
			output.write(HELP+"\n")
		elif query.command in Command.MAKE:
                    try:
                        args=docopt.docopt(Docs.MAKE,query.args)
                    except SystemExit as e:
                        print(e)
                        return
                    if args["index"]:
                        if args["id"]:
                            with self.indexdb() as indexdb:
                                createIdIndex(indexdb,self.db)
                        elif args["tag"]:
                            if args["kana"]:
                                with self.indexdb() as indexdb:
                                    createKanaOfTagIndex(indexdb,self.db)
                        elif args["all"]:
                            self.execQuery(__shell__.Query(("make","index","id")),output)
                            self.execQuery(__shell__.Query(("make","index","tag","kana")),output)
		elif query.command in Command.GET:
                    try:
                        args=docopt.docopt(Docs.GET,query.args)
                    except SystemExit as e:
                        print(e)
                        return
                    if args["recent"]:
                        if args["s"] or args["search"]:
                            sargs=args["<searchArgs>"]
                            sargs=list(util.arg_replace(sargs))
                            cards=self.search_card(sargs,output)
                            memo_length=20
                            with self.indexdb() as indexdb:
                                for card in cards:
                                    idxcards=getIndexCards(indexdb,self.db,card.comment(self.db.text))
                                    dates=list(map(lambda card:card.date,idxcards))
                                    if not dates:
                                        continue
                                    max_date=max(dates)
                                    memo=card.memo(self.db.text)
                                    if len(memo) > memo_length:
                                        memo=memo[:memo_length]+" ..."
                                    print(memo ,"->",max_date,file=output)
                    elif args["tag"]:
                        kana=args["<kana>"]
                        with self.indexdb() as indexdb:
                            cur=indexdb.cursor()
                            for tag in getTagFromKana(cur,self.db,kana+"%"):
                                print(tag,file=output)
                    else:
                        cardid=args["<cardid>"]
                        pMode=args["<pMode>"].upper() if args["-p"] else "M"
                        with self.indexdb() as indexdb:
                            cur=indexdb.cursor()
                            for card in getCardFromID(cur,self.db,cardid):
                                tagIdxes=self.db.cardToTags.get(card.id)
                                card=__index__.Card(card.memoIdx,card.commentIdx,tagIdxes,card.date)
                                csm=__data__.CSM.makeOne(self.db.text,card)
                                print("*",csm.dump(pMode),file=output)
                                print("-"*50,file=output)
		else:
			return super().execQuery(query,output)
	def search_card(self,args,output):
            try:
                args_=docopt.docopt(Docs.SEARCH_CARD,args)
            except SystemExit as e:
                print(e,args)
                return
            if args_["index"]:
                depth=int(args_["<depth>"] or 3)
                sargs=list(util.arg_replace(args_["<searchArgs>"]))
                cards=super().search_card(sargs,output)
                def getCards():
                    with self.indexdb() as indexdb:
                        for card in cards:
                            for icard in getIndexCards(indexdb,self.db,card.comment(self.db.text),depth=depth):
                                yield icard
                return getCards()
            else:
                return super().search_card(args,output)
	def search(self,args,output):
                try:
                    args_=docopt.docopt(Docs.SEARCH,args)
                except SystemExit as e:
                    print(e,args)
                    return
                if args_["index"]:
                    depth=args_["<depth>"] or str(3)
                    if args_["s"] or args_["search"]:
                            searchArgs=args_["<searchArgs>"]
                            cards=self.search_card(("index","--dp",depth,*searchArgs),output)
                    else:
                            query=""
                            if args_["-t"]:
                                tags=args_["<tags>"]
                                query+=f" /t {tags}"
                            if args_["-m"]:
                                memo=args_["<memo>"]
                                query+=f" /m {memo}"
                            cards=self.search_card(("index","--dp",depth,*query.strip().split()),output)
                    is_stdout=output is sys.stdout
                    pMode=args_["<pMode>"].upper()+"M" if args_["-p"] else "M"
                    data=""
                    for csm in __data__.CSM.make(self.db.text,cards):
                            data+="* "+csm.dump(pMode)+"\n"
                            data+="-"*50+"\n"
                    output.write(data)
                else:
                    return super().search(args,output)
	def start(self):
		if select2.iscrayon(self.stdout):
			self.stdout.write(crayons.magenta("*** ")+crayons.blue(self.db.id)+crayons.magenta(" ***\n"))
		else:
			self.stdout.write("*** "+self.db.id+" ***\n")
		__shell__.BaseShell3.start(self)
		self.close()

class AuHSShell(select2.AuHSShell):
	PROMPT=">>"
	SELECT_SHELL=DBShell
	def __init__(self,homeShell):
		super().__init__(homeShell)
		self.homeDB=homeShell.home
		self.environ={}
	def start(self):
		self.stdout.write("Don't find dbid.\n")
