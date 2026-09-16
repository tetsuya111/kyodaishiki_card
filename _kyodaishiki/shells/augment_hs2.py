from _kyodaishiki import __utils__
from _kyodaishiki import __shell__
from _kyodaishiki import __db__
from _kyodaishiki import __server__
from _kyodaishiki import __index__
from _kyodaishiki import __data__
from . import augment_hs
from . import util
import os
import docopt
import re
import json
import sys
from functools import *
import getpass
from hashlib import sha256

class Index:
	class DB(__index__.DB):
		def __init__(self,idIdx=__index__.Index(),pwIdx=__index__.Index()):
			super().__init__(idIdx)
			self.pwIdx=pwIdx
		def pw(self,text):
			return self.pwIdx.get(text)
		@property
		def locked(self):
			return self.pwIdx
		def __str__(self):
			return json.dumps((self.idIdx.data,self.pwIdx.data))
		@staticmethod
		def read(line):
			data=json.loads(line.rstrip())
			if len(data)==1:
				return Index.DB(__index__.Index(*data[0]))
			return Index.DB(__index__.Index(*data[0]),__index__.Index(*data[1]))


class ServerTagDB(__server__.ServerTagDB):
	EXPAND="~"
	NOT_GET_TAG_REC="+"
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
	def __searchForTag__(self,tags):
		def isexpand(tag):
			return tag and tag[0] == self.EXPAND
		def notGetTagRec(tag):
			return tag and tag[0] == self.NOT_GET_TAG_REC
#yield (tagIdx,card)
		def getTagIdxes(tags,U):
			tagexpander=util.TagExpander(self)
			tagIdxes__=list(map(lambda tag:self.getTagIdxesRec([tag],U),tags))
#<tags> => [<tagIdxes1>,...]
#<tagIdxes1> : cardIDs1 ,...
#res <tagIdxes1>&&<tagIdxes2>&&<tagIdxes3>,...
			def getExpanded(tagIdx):
				tag=tagIdx.get(self.text)
				if not tag:
					return
				if isexpand(tag):
					#tags=__data__.Logic.expandReg(tag[1:],allTags).split(__data__.Logic.OR)
					tags__=tagexpander.expand(tag[1:],U)
					for tagIdx__ in map(lambda tag:self.find(tag),tags__):
						yield tagIdx__
				else:
					yield tagIdx
			for tag in tags:
				rec=True
				if isexpand(tag):	#check expanded
					tags__=tagexpander.expand(tag[1:],U)
				elif notGetTagRec(tag):	#check expanded
					tags__=[tag[1:]]
					rec=False
				else:
					tags__=[tag]
				if rec:
				    tagIdxes=self.getTagIdxesRec(tags__,U)
				else:
                                    tagIdxes=\
                                        list(filter(bool,map(lambda tag:__data__.Logic.\
                                            Tag(tag=tag).toIndex(self.text).nameIdx,tags__)))
				yield util.reduce(lambda a,b:a+b,map(lambda tagIdx:list(getExpanded(tagIdx)),tagIdxes),init=[])
#tagIdxes => cardIDs
		def _getCardIDs(tagIdxes):
			for tagIdx in tagIdxes:
				res=self.tag.get(tagIdx)
				yield res.cardIDs if res else []
		def getCardIDs(tagIdxes):
			return util.reduce(lambda a,b:a+b,_getCardIDs(tagIdxes),init=[])
		def getData(tags,U):
			for tagIdxes in getTagIdxes(tags,U):
				yield __data__.Logic.Data(getCardIDs(tagIdxes))
		if not tags:
			for data in super().__searchForTag__(tags):
				yield data
			return
		U=self.getU()
		for cardID in util.reduce(lambda a,b:a.and_(b),getData(tags,U))(U):
			if self.get(cardID):
				yield (cardID,self.get(cardID))

class ServerHome(__server__.BaseServerHome):
	PORT=__server__.ServerHome.PORT
	def __init__(self,dname,host,aliasDBIDs={}):
		super().__init__(dname,host,CardDBClass=Index.DB,DBClass=ServerTagDB)
		self.aliasDBIDs=aliasDBIDs
	def appendAlias(self,aliasid,dbid):
		self.aliasDBIDs[aliasid.upper()]=dbid.upper()
	def getAlias(self,aliasid):
		dbid=aliasid.upper()
		while True:
			dbid=self.aliasDBIDs.get(dbid,"")
			if not dbid:
				return None
			if self.get(self.find(dbid)):
				return dbid
	def select(self,dbid,select_locked=True):
		dbid=dbid.upper()
		dbIdx=self.get(self.find(dbid))
		if not dbIdx or (dbIdx.locked and not select_locked):
			dbid=self.getAlias(dbid)
			if not dbid:
				return None
			return self.select(dbid)
		if dbIdx.locked:
			if not select_locked:
				return None
			else:
				pw=getpass.getpass(f"({dbid}) Password : ",stream=sys.stderr)
				if not self._checkpw(dbIdx,pw):
					return None
		return super().select(dbid)
	def _checkpw(self,dbIdx,pw):
		pw=sha256(pw.encode()).hexdigest()
		return pw==dbIdx.pw(self.text)
	def lock(self,dbid,pw):
		dbid=dbid.upper()
		db=self.get(self.find(dbid))
		if not db or db.locked:
			return False
		pw=sha256(pw.encode()).hexdigest()
		self.cards[self.find(dbid)].pwIdx=self.appendText(pw)
		return True
	def unlock(self,dbid,pw):
		dbid=dbid.upper()
		db=self.get(self.find(dbid))
		if not db or not db.locked:
			return False
		if self._checkpw(db,pw):
			self.cards[self.find(dbid)].pwIdx=__index__.Index()
			return True
		return False
	def __getDBIDs__(self,dbid):
		res=[]
		dbid=dbid.upper()
		dbid=__db__.compile_dbid(dbid)
		for aliasid in self.aliasDBIDs:
			if re.fullmatch(dbid,aliasid):
				dbid__=self.getAlias(aliasid)
				if dbid__:
					yield dbid__
		for dbid__ in super().getDBIDs(dbid):
			yield dbid__
	def getDBIDs(self,dbid):
		return set(self.__getDBIDs__(dbid))




class Docs:
	LS="""
	Usage:
		ls [(-p <pMode>)] [(-a|--all)]
	"""
	ALIAS="""
	Usage:
		alias db <aliasid> <dbid>
		alias (rm|remove) <command>
		alias <command> <query>...
	"""
	LOCK="""
	Usage:
		lock (u|un) <dbid>
		lock <dbid>
	"""
	HELP="""
# ls [(-a|--all)]
# lock [-u] <dbid>
# exec file <fname>
	"""

class Command:
	LOCK=("LOCK","LO")
	EXEC=("EX","EXEC")
	ALIAS=("ALS","ALIAS")


class HomeShell(augment_hs.HomeShell):
	PROMPT="%"
	def execQuery(self,query,output=sys.stdout):
		if not query:
			return
		if query.command in __utils__.Command.HELP:
			output.write(Docs.HELP+"\n")
			return super().execQuery(query,output)
		elif query.command in __utils__.Command.DB.LS:
			try:
				args=docopt.docopt(Docs.LS,query.args)
			except SystemExit as e:
				print(e)
				return
			all_=args["-a"] or args["--all"]
			pMode=args["<pMode>"].upper() if args["-p"] else ""
			cardToTags=self.home.cardToTags
			data=""
			for db in self.home.listDB():
				dbid=db.getID(self.home.text)
				tags=list(map(lambda tagIdx:tagIdx.get(self.home.text),cardToTags.get(db.id,[])))
				if not re.match("__",dbid) or all_:
					data+="ID:"+dbid.lower()
					if "T" in pMode:
						data+=" -> {0}".format(",".join(tags))
					if hasattr(db,"locked"):
						data+=" Locked" if db.locked else ""
					data+="\n"
					#print("ID:",db.getID(self.home.text).lower())
			output.write(data)
		elif query.command in Command.LOCK:
			try:
				args=docopt.docopt(Docs.LOCK,query.args)
			except SystemExit:
				return
			dbid=args["<dbid>"].upper()
			if args["u"] or args["un"]:
				pw=getpass.getpass()
				for dbid__ in self.home.getDBIDs(dbid):
					if self.home.unlock(dbid__,pw):
						output.write("Unlocked "+dbid__+"\n")
					else:
						output.write("Unlock failed. (db isn't locked or pw is illegal or etc...)\n")
			else:
				pw=getpass.getpass()
				pw_for_check=getpass.getpass("Password (check) : ")
				if pw != pw_for_check:
					print("Password is deference.",file=output)
					return
				for dbid__ in self.home.getDBIDs(dbid):
					if self.home.lock(dbid__,pw):
						output.write("Locked "+dbid__+"\n")
		elif query.command in __utils__.Command.DB.SERVER:
			if query.args and query.args[0]=="start":
				super().execQuery(query,output)
				super().execQuery(__shell__.Query(("server","stop","__*")),output)
			else:
				super().execQuery(query,output)
		elif query.command in Command.ALIAS:
			return self.alias(query.args,output)
		else:
			return super().execQuery(query,output)
	def alias(self,args__,output):
		if args__ and args__[0] not in ("rm","remove","db"):
			return super().alias(args__,output)
		try:
			args=docopt.docopt(Docs.ALIAS,args__)
		except SystemExit as e:
			output.write("*** db ***\n")
			for aliasid in self.home.aliasDBIDs:
				output.write("{0} -> {1}\n".format(aliasid.lower(),self.home.aliasDBIDs[aliasid].lower()))
			return super().alias(args__,output)
		if args["db"]:
			aliasid=args["<aliasid>"]
			dbid=args["<dbid>"]
			self.home.appendAlias(aliasid.upper(),dbid.upper())
			output.write("Alias db {0} as {1}\n".format(dbid,aliasid))
		else:
			return super().alias(args__,output)

def loadHome(dname,host="127.0.0.1"):
	home=ServerHome(dname,host)
	return HomeShell(home)
