import sys
import docopt
import re
import os
import csv
import zlib
from _kyodaishiki import _util
from _kyodaishiki import __data__
from _kyodaishiki import __shell__
from _kyodaishiki import __db__
from . import util
from . import augment_hs
from . import mecab
from . import category
import copy
import _pyio
import subprocess as sp
import random
import shutil
import datetime
import crayons
import colorama
import winshell

class Attr(util.Attr):
	DBID="DBID"
	USERID="USERID"

class EnvKey:
	WRITE_TAGS="WRITETAGS"
	PORT="PORT"

NOT="__NOT__"
TMP_NOT="__TMP_NOT__"
ALL_NOT_L=(NOT,TMP_NOT)
ALL_NOT="||".join(ALL_NOT_L)


TMP=lambda:str(random.randint(10**25,10**35))+".tmp"


def grep(s,reg):
	reg=re.compile(reg)
	for line in s.split("\n"):
		if re.search(reg,line):
			yield line

def getMemo(dname):
	for fname in os.listdir(dname):
		if not ".csm" in fname:
			continue
		fname=os.path.join(dname,fname)
		csm=__data__.CSM.read(fname)
		if not __data__.TOT.isTOT(csm):
			yield csm.memo

def getWords(text):
	for word,data in mecab.Mecab.__analize__(text):
		if word=="EOS" or (data and "\\xe3\\x80\\x82" in str(word.encode())):
			continue
		if b'\xe5\x90\x8d\xe8\xa9\x9e'.decode() in data[0]:
			yield word

def writeW(output=sys.stdout):
	csm=__shell__.Shell.write()
	csm.tags=(*csm.tags,*set(getWords(csm.memo)))
	return csm
def writeL(output=sys.stdout):
    title=input("Title( blank OK ) : ")
    def getList():
        category_name=input("Category Name : ")
        if not category_name:
            return None
        cate=util.Category(title=category_name,childs=[])
        print(f"*** {cate.title} ***",file=output)
        history=[]
        cols=[]
        while True:
            data=input("col or category name (start with ^ ) : ")
            if data and data[0] == "^":
                cate.data=(cate.data[0],(*cate.cols,*cols))
                cols=[]
                title=data[1:]
                cate_child=util.Category(title=title,childs=[])
                cate.childs.append(cate_child)
                history.append(cate)
                cate=cate_child
                print(f"*** {cate.title} ***",file=output)
            elif not data:
                cate.data=(cate.data[0],(*cate.cols,*cols))
                cols=[]
                if not history:
                    break
                cate=history.pop()
                print(f"*** {cate.title} ***",file=output)
            else:
                cols.append(data)
        return cate
    cate=getList()
    if not cate:
        return None
    comment=str(cate)
    print(comment)
    tags=list(_util.inputUntilSeq("Tag : ",output=output))
    date=str(datetime.datetime.now()).split(".")[0]
    if not title:
        hashed=str(zlib.adler32(comment.encode()))
        title="{0}-{1}-{2}".format(date,hashed,",".join(tags))
    return __data__.CSM(title,comment,tags,date)

def addlowUp(base,s):
	return util.addMemo(base,util.tolowUp(s))
	
def writeShell():
	memo_text="{0} : ".format(b'\xe3\x83\xa1\xe3\x83\xa2'.decode())
	memo="\n".join(_util.inputUntilSeq(memo_text))
	comment_text="{0} : ".format(b'\xe3\x82\xb3\xe3\x83\xa1\xe3\x83\xb3\xe3\x83\x88'.decode())
	comment="\n".join(_util.inputUntilSeq(comment_text))
	tags=list(_util.inputUntilSeq("{0} : ".format(b'\xe3\x82\xbf\xe3\x82\xb0'.decode())))
	date=str(datetime.datetime.now()).split(".")[0]
	return __data__.CSM(memo,comment,tags,date)

def iscrayon(f):
	return type(f) is colorama.ansitowin32.StreamWrapper

class QueryHistory:
    DEF_FNAME="se2_command_history.txt"
    def __init__(self,dname=None,fname=None):#,n=100):
        self.dname=dname
        self.fname=fname or self.DEF_FNAME
        self.queries=[]
        if dname:
            fname=fname or self.DEF_FNAME
            fname=os.path.join(dname,fname)
            self.queries=list(self.read(fname))
            #if len(self.queries) > n:
            #    self.queries=self.queries[len(self.queries)-n:-1]
    def clear(self):
        self.queries=[]
    def append(self,query):
        self.queries.append(query)
    def __iter__(self):
        return iter(self.queries)
    def read(self,fname,encoding="utf8"):
        if not os.path.exists(fname):
            return
        with open(fname,"r",encoding=encoding) as f:
            for line in f.readlines():
                line=line.rstrip()
                query=__shell__.Query.read(line)
                yield query
    def write(self,fname,mode="w+",encoding="utf8"):
        with open(fname,mode,encoding=encoding) as f:
            for query in self.queries:
                f.write(str(query)+"\n")
    def save(self):
        if not self.dname:
            return
        fname=self.fname or self.DEF_FNAME
        fname=os.path.join(self.dname,fname)
        return self.write(fname,mode="w")

def _search_rec_by_tag(db,cards,depth=1,tag_n=3,now_depth=0,now_key=None,hashes=[]):
    def getid(card):
        return hash(str(card))
    def getTags(cards):
        data={}
        for card in cards:
            tags=card.tags(db.text)
            for tag in tags:
                if not data.get(tag):
                    data[tag]=0
                data[tag]+=1
        return data
    if now_depth >= depth:
        return {}
    cards=list(filter(lambda card:getid(card) not in hashes,cards))
    tag_data=getTags(cards)
    #print("tag_data",tag_data)
    hashes.extend(map(getid,cards))
    keys=sorted(tag_data,key=lambda key:tag_data[key],reverse=True)
    keys=list(keys)[:tag_n]
    res={now_depth:[{"key":now_key,"cards":cards}]}
    for key in keys:
        cards=db.search(tags=[key])
        res__=_search_rec_by_tag(db,cards,depth,tag_n,now_depth=now_depth+1,now_key=key,hashes=hashes)
        if not res__:
            continue
        for res_depth in res__:
            data=res__[res_depth]
            if res_depth not in res:
                res[res_depth]=[]
            res[res_depth].extend(data)
    return res
def search_rec_by_tag(db,cards,depth=1,tag_n=3):
    return _search_rec_by_tag(db,cards,depth=depth,tag_n=tag_n,\
        now_depth=0,hashes=[])

class Docs:
	class CSM:
		WRITE="""
		Usage:
			write tot [(-t <tag>)] [(-d <dname>)]
			write csm (s|search) [(-d <dname>)] [<searchArgs>...]
			write csm [(-t <tags>)] [(-m <memo>)] [(-d <dname>)]
			write [(-d <dname>)] [(--at <appendTags>)] [(--ad|--append-dbid)] 
		"""
		APPEND="""
		Usage:
			append tot [(-e|--edit)] [(-O|--override)] [(-t <tag>)] [(-d <dname>)]
			append csm (s|search) [(-e|--edit)] [(-O|--override)] [(-d <dname>)] <searchArgs>...
			append csm [(-e|--edit)] [(-O|--override)] [(-t <tags>)] [(-m <memo>)] [(-d <dname>)] 
			append [(-d <dname>)] [(-O|--override)] [(--dp <depth>)]
		"""
		REMOVE="""
		Usage:
			remove
		"""
#"append" is for original execQuery.
	WRITE="""
	Usage:
		write tot
		write (w|word)
                write (l|list)
		write
	"""

	SEARCH="""
	Usage:
                search rec (t|bytag) [(--dp <depth>)] [(--tn <tag_n>)] <searchArgs>...
		search (n|not) [(-t <tags>)] [(--nt <noTags>)] [(-m <memo>)] [(--mm <lowUpMemo>)] [(--em <escapedMemo>)] [(-c <comment>)] [(-F <from>)] [(-U <until>)] [(-u <userid>)] [(-D <dbid>)] [(-p <pMode>)] [(-r|--random)] [(--al|--aslist)]
                search [(-t <tags>)] [(--nt <noTags>)] [(-m <memo>)] [(--mm <lowUpMemo>)] [(--em <escapedMemo>)] [(-c <comment>)] [(-a <all_text>)] [(-F <from>)] [(-U <until>)] [(-u <userid>)] [(-D <dbid>)] [(--pn|--printNot)] [(-p <pMode>)] [(-r|--random)]
	"""
	SEARCH_CARD="""
	Usage:
		search_card [(-t <tags>)] [(--nt <noTags>)] [(-m <memo>)] [(--mm <lowUpMemo>)] [(--em <escapedMemo>)] [(-c <comment>)] [(-a <all_text>)] [(-F <from>)] [(-U <until>)] [(-u <userid>)] [(-D <dbid>)] [(--pn|--printNot)]
	"""
	LIST="""
	Usage:
		list tot [<tag>]  [(-a|--all)] [(-r|--random)]
		list (t|tag) (s|search) [(-r|--random)] [<searchArgs>...]
		list (t|tag) [<tag>] [(-r|--random)]
	"""
	REMOVE="""
	Usage:
		remove memo [(-d <dname>)]
		remove tag (s|search) <_searchArgs> <removedTags>...
		remove tag [(-t <tags>)] [(-m <memo>)] [(-F <from>)] [(-U <until>)] <removedTags>...
		remove tot [<tag>]
		remove (s|search) <searchArgs>...
		remove [(-t <tags>)] [(-m <memo>)] [(-u <userid>)] [(-D <dbid>)]
	"""
	APPEND="""
	Usage:
		append tag (w|word) [<searchArgs>...]
		append tag (s|search) <searchArgs__> <tagsToAppend>...
		append tag [(-t <tags>)] [(-m <memo>)] [(-F <from>)] [(-U <until>)] <tagsToAppend>...
                append csv <fname> [(-t <tags>)] [(-O|--override)]
	"""
	ALTER="""
	Usage:
		alter (s|search) [--tmp] <searchArgs>...
		alter [(-t <tags>)] [(-m <memo>)] [--tmp]
	"""
	NUMBER="""
	Usage:
		number (s|search) [<searchArgs>...]
		number [(-t <tags>)] [(-m <memo>)]
	"""
	EXPAND="""
	Usage:
		expand auto [(-O|--override)]
		expand [(-t <tags>)] [(-m <memo>)] [(-O|--override)]
	"""
	VIM="""
	Usage:
		vim (f|file) <fname>
        vim (als|alias)
		vim enter
		vim exit
		vim stdin [(-d <dname>)]
		vim tot [(-t <tag>)] [(-r|--random)]
		vim (s|search) [(-n <number>)] [(-d <dname>)] [(-r|--random)] [<searchArgs>...]
		vim [(-t <tags>)] [(--nt <noTags>)] [(-m <memo>)] [(-c <comment>)] [(-F <from>)] [(-U <until>)] [(--pn|--printNot)] [(-n <number>)] [(-d <dname>)] [(-r|--random)]
	
	Options:
		searchArgs : "-" to "/". ex) vim s -t book -> vim /t book
	"""
	DUMP="""
	Usage:
		dump csv [(-t <tags>)] [(-m <memo>)] [(-p <pMode>)]
		dump (c|category) [(-T <titles>)] [(-t <tags>)] [(-m <memo>)]
	"""
	LINK="""
	Usage:
		link (s|search) [(-p <pMode>)] [<searchArgs>...]
		link [(-t <tags>)] [(-m <memo>)] [(-p <pMode>)]
	"""
	COUNT="""
	Usage:
		count (ln|link) [<searchArgs>...]
                count (c|col) [<searchArgs>...]
		count (w|word) [<searchArgs>...]
		count [(-R|--reverse)] [(-f <from>)] [(-u <until>)] [(-m <mode>)] [(-p <pMode>)] [<searchArgs>...]

        Options:
                <from>  : from the number of count
                <until>  : until the number of count
                <mode> : M:memo,C:comment,T:tag,A:all.Including text to count number.
                <pMode> : F : fname.Print mode.
	"""
	HISTORY="""
	Usage:
               history ls
               history clear
	"""
	INDEX="""
        Usage:
            index <args>...
	"""
	GREP="""
        Usage:
            grep <text> [<searchArgs>...]
	"""
	SET="""
	Usage:
		set [<key>]
		set <key> <value>
	"""
	HELP="""
	Usage:
		help [(-a|--all)]
	"""
HELP="""
	help [(-a|--all)]
	csm write
	csm append
	csm remove
	search
	remove
	number
	append
	alter
	expand
	dump
	vim ...
	vlc
	alias
	set
"""

class Command(util.Command):
	ALTER=("AL","ALTER")
	VIM=["VIM"]
	ADMIT=("AD","ADMIT")
	ALIAS=("ALS","ALIAS")
	EXPAND=("EXP","EXPAND")
	DUMP=("D","DUMP")
	LINK=("LN","LINK")
	COUNT=("CN","COUNT")
	HISTORY=("HS","HISTORY")
	GREP=["GREP"]
	INDEX=("IDX","INDEX")
	SET=["SET"]
	SEARCH_CARD=["SEARCH_CARD"]

class DBShell(__shell__.DBShell,__shell__.BaseShell3):
	VIM_MAX=50
	VIM_COUNT_OF_FILE=50
	PROMPT=str(crayons.magenta(">>"))
	#PROMPT=">>"
	def __init__(self,db,expander=None,environ={},stdout=sys.stdout):
		__shell__.DBShell.__init__(self,db)
		__shell__.BaseShell3.__init__(self,db.dname,self.PROMPT)
		self.dname=db.dname
		self.expander=expander
		self.environ=environ
		self.stdout=stdout
		os.environ["KYODAISHIKI_DB_DIR"]=db.dname
		os.environ["KYODAISHIKI_DB_ID"]=db.id
		#self.query_history=QueryHistory(db.dname)
		self.query_history=QueryHistory(None)
#append tmp_not as child of not	
			
	def execQuery(self,query,output=sys.stdout):
		if query.command not in Command.HISTORY:
                    self.query_history.append(query)
		if query.command in _util.Command.HELP:
			try:
				args=docopt.docopt(Docs.HELP,query.args)
			except SystemExit:
				return
			output.write("*** select2 ***\n")
			output.write(HELP+"\n")
			if args["-a"] or args["--all"]:
				output.write("*** select ***\n")
				return __shell__.DBShell.execQuery(self,query,output)
		elif query.command in _util.Command.WRITE:
			try:
				args=docopt.docopt(Docs.WRITE,query.args)
			except SystemExit as e:
				print(e)
				return
			if args["w"] or args["word"]:
				csm=writeW()
				self.db.appendCSM(csm)
			elif args["l"] or args["list"]:
                            csm=writeL()
                            if not csm:
                                return
                            self.db.appendCSM(csm)
			elif args["tot"]:
				return super().execQuery(query,output)
			else:
				def getWriteTags():
                                    for key in self.environ:
                                        a=re.match(f"{EnvKey.WRITE_TAGS}_(?P<attr>.+)",key)
                                        if not a:
                                            continue
                                        attr=a.group("attr")
                                        yield f"{attr}:{self.environ[key]}"
				tags=self.environ.get(EnvKey.WRITE_TAGS)
				#print("tags",tags)
				tags=tags.upper().split(",") if tags else []
				csm=writeShell()
				csm.tags=(*csm.tags,*tags,*getWriteTags())
				self.db.appendCSM(csm)
			self.db.save()
		elif query.command in _util.Command.SEARCH:
			try:
				return self.search(query.args,output)
			except KeyboardInterrupt as e:
				return
			except Exception as e:
				print(e,query)
			except SystemExit as e:
				print(e)
		elif query.command in Command.SEARCH_CARD:
			try:
				return self.search_card(query.args,output)
			except KeyboardInterrupt as e:
				return
			except Exception as e:
				print(e,query)
		elif query.command in _util.Command.LIST:
			try:
				args=docopt.docopt(Docs.LIST,query.args)
			except SystemExit as e:
				print(e)
				return
			tag=args["<tag>"].upper() if args["<tag>"] else str()
			if args["tot"]:
				all_=args["-a"] or args["--all"]
				if tag:
					U=self.db.getU()
					tots=self.db.searchTOT(tag)
				else:
					tots=self.db.tots.values()
				if args["-r"] or args["--random"]:
					tots=list(tots)
					random.shuffle(tots)
				for tot in tots:
					if all_:
						c=util.Category.make_from_tot(tot,self.db.tots,self.db.text)
						data=str(c)+"\n"
					else:
						tot__=__data__.Logic.Group.makeFromIndex(tot.nameGroup,self.db.text)
						data="* "+str(tot__)
					output.write(data+"\n")
			else:
				if args["s"] or args["search"]:
					random_=args["-r"] or args["--random"]
					searchArgs=args["<searchArgs>"]
					searchArgs=util.arg_replace(searchArgs)
					cards=self.execQuery(__shell__.Query(("search_card",*searchArgs)),output)
					cards=list(cards)
					if not cards:
						return
					if len(cards) == 1:
						tags=cards[0].tags(self.db.text)
						data=map(lambda tag:(tag,1),tags)
					else:
						def ls_tag_getData(cards):
							res={}
							for card in cards:
								tags=card.tags(self.db.text)
								for tag in tags:
									if not res.get(tag):
										res[tag]=0
									res[tag]+=1
							return res
						data=ls_tag_getData(cards).items()
					if random_:
						data=list(data)
						random.shuffle(data)
					else:
						data=sorted(data,key=lambda dat:dat[1])
					sio=_pyio.StringIO()
					for tag,n in data:
						print(tag,n,file=sio)
					sio.seek(0)
					print(sio.read())
				else:
					tag=re.compile(tag)
					tags=filter(lambda tag__:re.search(tag,tag__),self.db.getTags())
					data=[]
					for tag__ in tags:
						tagobj= self.db.tag.get(self.db.find(tag__))
						if tagobj:
							data.append((tag__,len(tagobj.cardIDs)))
					if args["-r"] or args["--random"]:
						data=list(data)
						random.shuffle(data)
					else:
						data=sorted(data,key=lambda data__:data__[1])
					res=""
					for tag__,n in data:
						res+=tag__+" "+str(n)+"\n"
					output.write(res)
					data=map(lambda tag__:( tag__,len( self.db.tag.get(self.db.find(tag__)).cardIDs ) ),tags)   #[(<tag>,<n>),...]

		elif query.command in _util.Command.REMOVE:
			try:
				args=docopt.docopt(Docs.REMOVE,query.args)
			except SystemExit as e:
				print(e)
				return
			if args["memo"]:
				dname=args["<dname>"] if args["-d"] else util.DEFAULT_CSM_DIR_F(self.db.dname)
				with open(TMP(),"w+") as f:
					f.write("\n".join(map(lambda memo:'rm -m "{0}"'.format(memo),getMemo(dname))))
					f.seek(0,0)
					return super().__begin__(f,output)
			elif args["tag"]:
			#remove tag (s|search) <searchArgs> <removedTags>...
			#remove tag [(-t <tags>)] [(-m <memo>)] [(-F <from>)] [(-U <until>)] <removedTags>...
			#remove tot [<tag>]
			#remove tag (s|search) <searchArgs>...
				removedTags=args["<removedTags>"]
				if args["s"] or args["search"]:
					#searchArgs=args["<searchArgs>"]
					searchArgs=__shell__.Query.read(args["<_searchArgs>"])
					cards=self.execQuery(__shell__.Query(("search_card",*util.arg_replace(searchArgs))),output)

				else:
					memo=args["<memo>"] if args["-m"] else ""
					tags=args["<tags>"].upper().split(",") if args["-t"] else []
					from_=args["<from>"] if args["-F"] else "1900-1-1"
					until=args["<until>"] if args["-U"] else "2200-1-1"
					from_=util.to_datetime(from_)
					until=util.to_datetime(until)
					cards=filter(lambda card:from_<=util.to_datetime(card.date)<until,list(self.db.search(memo,tags)))
				cards=list(cards)
				self.db.__removeTags__(map(lambda card:card.id,cards),removedTags)
				for card in cards:
					output.write("Remove {0} from {1}\n".format(str(removedTags),card.memo(self.db.text)))
			elif args["tot"]:
				return __shell__.DBShell.execQuery(self,query,output)
			else:
				if args["s"] or args["search"]:
					searchArgs=args["<searchArgs>"]
					cards=self.execQuery(__shell__.Query(("search_card",*util.arg_replace(searchArgs))),output)
				else:
					memo=args["<memo>"] if args["-m"] else ""
					tags=args["<tags>"].upper().split(",") if args["-t"] else []
					if args["-u"]:
						tags.append(Attr.to_format(Attr.USERID).format(args["<userid>"].upper()))
					if args["-D"]:
						tags.append(Attr.to_format(Attr.DBID).format(args["<dbid>"].upper()))
					if not memo and not tags:
						output.write("You will remove all cards. Really OK??(.../n) : ")
						yn=input()
						if yn.upper()!="Y":
								return 
					cards=self.db.search(memo,tags)
				for card in list(cards):
					#csm=__data__.CSM.makeOne(self.db.text,card)
					self.db.remove(card.id)
					output.write("Removed "+card.memo(self.db.text)+"\n")
				self.db.save()

		elif query.command in _util.Command.CSM:
			query=__shell__.Query(query.args)
			if query.command in _util.Command.WRITE:
				try:
					args=docopt.docopt(Docs.CSM.WRITE,query.args)
				except SystemExit as e:
					print(e,query.args)
					return
				dname=args["<dname>"] if args["-d"] else util.DEFAULT_CSM_DIR_F(self.db.dname)
				dname=_util.realpath(dname)
				if not os.path.exists(dname):
					os.makedirs(dname)
				if args["tot"] :
					tag=args["<tag>"] if args["-t"] else ""
					for tot in list(__data__.TOT.make(self.db.text,self.db.searchTOT(tag))):
						tot.write(os.path.join(dname,tot.fname))
				elif args["csm"]:
					if args["s"] or args["search"]:
						searchArgs=list(util.arg_replace(args["<searchArgs>"]))
						cards=self.search_card(searchArgs,output)
					else:
						memo=args["<memo>"] if args["-m"] else str()
						tags=args["<tags>"].upper().split(",") if args["-t"] else list()
						regDBID_TAG=re.compile(Attr.DBID)
						cards=self.db.search(memo,tags)
					for csm in list(__data__.CSM.make(self.db.text,cards)):
						csm.write(os.path.join(dname,csm.fname))
				else:
					#__shell__.CSMShell2(self.db).execQuery(__shell__.Query(("WRITE","-d",dname)),output)
                                        tags=args["<appendTags>"].upper().split(",") if args["--at"] else []
                                        if args["--ad"] or args["--append-dbid"]:
                                            dbidtag=Attr(Attr.DBID).format(self.db.id).upper()
                                            tags=(*tags,dbidtag)
                                        if __shell__.CSMShell2.is_CSM_DB(self.db):
                                                for csm in self.db.dumpCSM():
                                                    if tags:
                                                        csm.tags=(*csm.tags,*tags)
                                                    csm.write(os.path.join(dname,csm.fname))
                                        if __shell__.CSMShell2.is_TOT_DB(self.db):
                                                for tot in self.db.dumpTOT():
                                                        tot.write(os.path.join(dname,tot.fname))
                                        print("Written in",dname,file=sys.stderr)
			elif query.command in _util.Command.APPEND:
				try:
					args=docopt.docopt(Docs.CSM.APPEND,query.args)
				except SystemExit as e:
					print(e)
					return
				dname=args["<dname>"] if args["-d"] else util.DEFAULT_CSM_DIR_F(self.db.dname)
				dname=_util.realpath(dname)
				if args["tot"] :
					tag=args["<tag>"] or ""
					override=args["-O"] or args["--override"]
					regTag=re.compile(tag)
					edit=args["-e"] or args["--edit"]
					if edit:
						basetots=__data__.TOT.make(self.db.text,self.db.searchTOT(tag))
						fnames=map(lambda tot:os.path.join(dname,tot.fname),basetots)
						fnames=filter(lambda fname:os.path.exists(fname),fnames)
						csms=map(lambda fname:__data__.CSM.read(fname),fnames)
					else:
						csms=__data__.CSM.readDir(dname)
					for csm in list(csms):
						if __data__.TOT.isTOT(csm):
							tot=__data__.TOT.toTOT(csm)
							if re.search(regTag,tot.name):
								if self.db.appendTOT(tot.name,tot.childs,override):
									output.write("Appended {0}\n".format(tot.name))
				elif args["csm"]:
					if args["s"] or args["search"]:
						searchArgs=list(util.arg_replace(args["<searchArgs>"]))
						cards=self.search_card(searchArgs,output)
						edit=True
					else:
						memo=args["<memo>"] if args["-m"] else ""
						tags=args["<tags>"].upper().split(",") if args["-t"] else []
						cards=self.db.search(memo,tags)
						edit=args["-e"] or args["--edit"]
					override=args["-O"] or args["--override"]
					text=""
					if edit:
						basecsms=__data__.CSM.make(self.db.text,cards)
						fnames=map(lambda tot:os.path.join(dname,tot.fname),basecsms)
						fnames=filter(lambda fname:os.path.exists(fname),fnames)
						csms=map(lambda fname:__data__.CSM.read(fname),fnames)
					else:
						csms=__data__.CSM.readDir(dname)
						csms=filter(lambda csm:not __data__.TOT.isTOT(csm),csms)
						csms=filter(lambda csm:(not memo or re.search(memo,csm.memo)) and (not tags or all([tag in csm.tags for tag in tags])),csms)
					for csm in list(csms):
						if self.db.appendCSM(csm,override):
							text+="Appended {0}\n".format(csm.memo)
					output.write(text)
				else:
					query,_,_=util.partitionArgs(query.data,("-d","-r","--rec"))
					query=__shell__.Query(query)
					dname=args["<dname>"] or util.DEFAULT_CSM_DIR_F(self.db.dname)
					dname=_util.realpath(dname)
					rec=args["--dp"]
					depth=int(args["<depth>"]) if rec else 0
					default_depth=dname.count("\\")
					__shell__.DBShell.execQuery(self,__shell__.Query(("CSM",*query.data,"-d",dname)),output)
					if rec:
						for cur,ds,fs in os.walk(dname):
							if cur.count("\\") > depth+default_depth:
								continue
							for dname__ in ds:
								dname__=os.path.join(cur,dname__)
								__shell__.DBShell.execQuery(self,__shell__.Query(("CSM",*query.data,"-d",dname__)),output)
					#if "-d" not in query:
					#	query.extend(("-d",util.DEFAULT_CSM_DIR_F(self.db.dname)))
				self.db.save()
			elif query.command in Command.REMOVE:
				csm_dname=util.DEFAULT_CSM_DIR_F(self.db.dname)
				winshell.delete_file(csm_dname)
				output.write("Removed {0}\n".format(csm_dname))
			else:
				if "-d" not in query:
					query.extend(("-d",util.DEFAULT_CSM_DIR_F(self.db.dname)))
				__shell__.DBShell.execQuery(self,__shell__.Query(("CSM",*query.data)),output)
		elif query.command in _util.Command.APPEND:
			try:
				args=docopt.docopt(Docs.APPEND,query.args)
			except SystemExit as e:
				print(e)
				return
			if args["tag"]:
				if args["w"] or args["word"]:
					searchArgs=util.arg_replace(args["<searchArgs>"])
					cards=self.search_card(searchArgs,output)
					for card in list(cards):
						memo=card.memo(self.db.text)
						words=list(getWords(memo))
						self.db.appendTags(card.id,words)
						output.write("Append "+str(words)+" to "+card.memo(self.db.text)+"\n")
					return
				tagsToAppend=list(map(lambda tag:tag.upper(),args["<tagsToAppend>"]))
				if args["s"] or args["search"]:
					searchArgs=util.arg_replace(__shell__.Query.read("search_card "+args["<searchArgs__>"]).data)
					cards=self.execQuery(__shell__.Query(searchArgs),output)
				else:
					memo=args["<memo>"] if args["-m"] else str()
					tags=args["<tags>"].upper().split(",") if args["-t"] else []
					from_=args["<from>"] if args["-F"] else "1900-1-1"
					until=args["<until>"] if args["-U"] else "2200-1-1"
					from_=util.to_datetime(from_)
					until=util.to_datetime(until)
					cards=filter(lambda card:from_<=util.to_datetime(card.date)<until,list(self.db.search(memo,tags)))
				for card in list(cards):
					self.db.appendTags(card.id,tagsToAppend)
					output.write("Append "+str(tagsToAppend)+" to "+card.memo(self.db.text)+"\n")
			if args["csv"]:
                            fname=_util.realpath(args["<fname>"])
                            override=args["-O"] or args["--override"]
                            base_tags=args["<tags>"].upper().split(",") if args["-t"] else []
                            encoding="utf8"
                            with open(fname,"r",encoding=encoding) as f:
                                reader=csv.reader(f)
                                headers=next(reader)
                                for col in reader:
                                    data=dict(zip(headers,col))
                                    if not data.get("memo"):
                                        continue
                                    tags=data["tags"].upper().split() if data.get("tags")\
                                        else []
                                    tags=(*base_tags,*tags)
                                    self.db.append(
                                        data["memo"],
                                        data.get("comment") or "",
                                        tags,
                                        data.get("date") or "1900-1-1",
                                        override
                                    )
                                print("Appended",fname,file=output)
			self.db.save()
		elif query.command in Command.ALTER:
			try:
				args=docopt.docopt(Docs.ALTER,query.args)
			except SystemExit as e:
				print(e)
				return
			if args["s"] or args["search"]:
				searchArgs=args["<searchArgs>"]
				searchArgs=util.arg_replace(searchArgs)
				cards=self.execQuery(__shell__.Query(("search_card",*searchArgs)),output)
			else:
				memo=args["<memo>"] if args["-m"] else str()
				tags=args["<tags>"].upper().split(",") if args["-t"] else []
				if not (memo or tags):
					print("Try to alter all card.OK?? (y/n...) : ",file=sys.stderr,end="")
					yn=input().upper()
					if yn != "Y":
						return
				cards=self.db.search(memo,tags)
			s=""
			if args["--tmp"]:
				tags=[TMP_NOT]
			else:
				tags=[NOT]
			for card in list(cards):
				if any(map(lambda tag:tag in ALL_NOT_L,\
					card.tags(self.db.text))):
					self.db.removeTags(card.id,tags)
				else:
					self.db.appendTags(card.id,tags)
				s+="Altered "+card.memo(self.db.text)+"\n"
			output.write(s)
			self.db.save()
		elif query.command in Command.EXPAND:
			if not self.expander:
				output.write("Don't find expander.\n")
				return
			try:
				args=docopt.docopt(Docs.EXPAND,query.args)
			except SystemExit as e:
				print(e)
				return
			if args["auto"]:
				override=args["-O"] or args["--override"]
				data=""
				for csm in __data__.CSM.make(self.db.text,list(self.db.search())):
					if util.Expander.TAG in csm.tags: #maybe expanded
						continue
					if not re.search(f"^{util.Expander.EXPAND_HEAD}",csm.comment,flags=re.MULTILINE):
						continue
					csm__=self.expander.expand(csm)
					if not override:
						csm__.memo="__"+csm__.memo
					self.db.appendCSM(csm__,True)
					data+="Append {0} \n".format(csm__.memo)
				print(data,file=output)
			else:
				tags=args["<tags>"].upper().split(",") if args["-t"] else []
				memo=args["<memo>"] if args["-m"] else ""
				override=args["-O"] or args["--override"]
				data=""
				for csm in list(__data__.CSM.make(self.db.text,self.db.search(memo,tags))):
					if util.Expander.TAG in csm.tags: #maybe expanded
						continue
					csm__=self.expander.expand(csm)
					if not override:
						csm__.memo="__"+csm__.memo
					self.db.appendCSM(csm__,True)
					data+="Append {0} \n".format(csm__.memo)
				output.write(data)
		elif query.command in Command.VIM:	#-Z for can't use shell query.command in vim.
			try:
				args=docopt.docopt(Docs.VIM,query.args)
			except SystemExit as e:
				print(e)
				return
			if args["f"] or args["file"]:
				fnames=[_util.realpath(args["<fname>"])]
			elif args["als"] or args["alias"]:
				if self.alias_txt:
					fnames=[self.alias_txt]
			elif args["enter"]:
				if self.enterBat:
					fnames=[self.enterBat]
			elif args["exit"]:
				if self.exitBat:
					fnames=[self.exitBat]
			elif args["stdin"]:
                            dname=args["<dname>"] or util.DEFAULT_CSM_DIR_F(self.db.dname)
                            text=sys.stdin.read()
                            def _():
                                hashes=[]
                                def validate(fname):
                                    fname=os.path.join(dname,fname)
                                    hashed=hash(fname)
                                    if hashed not in hashes:
                                        hashes.append(fname)
                                        return fname
                                    return None
                                for fname in (*re.findall("C\\.*\\[0-9]+\.csm",text),\
                                        *re.findall("[0-9]+.csm",text)):
                                    res=validate(fname)
                                    if res:
                                        yield res
                            fnames=list(_())
			elif args["tot"]:
				dname=args["<dname>"] if args["-d"] else util.DEFAULT_CSM_DIR_F(self.db.dname)
				dname=_util.realpath(dname)
				tag=args["<tag>"].upper() if args["-t"] else ""
				tots=__data__.TOT.make(self.db.text,self.db.searchTOT(tag))
				fnames=list(map(lambda tot:os.path.join(dname,tot.fname),tots))
			elif args["s"] or args["search"]:
				dname=args["<dname>"] if args["-d"] else util.DEFAULT_CSM_DIR_F(self.db.dname)
				dname=_util.realpath(dname)
				random_=args["-r"] or args["--random"]
				searchArgs=util.arg_replace(args["<searchArgs>"])
				sio=_pyio.StringIO()
				self.execQuery(__shell__.Query(("search",*searchArgs,"-p","f")),sio)
				sio.seek(0)
				def get_fnames():
					for line in sio.read().split("\n"):
						if line.find("*") != 0 and ".csm" in line:
							yield line
				fnames=map(lambda fname:os.path.join(dname,fname),get_fnames())
				fnames=filter(lambda fname:os.path.exists(fname),fnames)
				if random_:
					fnames=list(fnames)
					random.shuffle(fnames)
			else:
				memo=args["<memo>"] if args["-m"] else ""
				tags=args["<tags>"].upper().split(",") if args["-t"] else []
				noTags=args["<noTags>"].upper().split(",") if args["--nt"] else []
				comment=args["<comment>"] if args["-c"] else ""
				from_=util.to_datetime(args["<from>"]) if args["-F"] else util.to_datetime("1900-1-1")
				until=util.to_datetime(args["<until>"]) if args["-U"] else util.to_datetime("2200-1-1")
				dname=args["<dname>"] if args["-d"] else util.DEFAULT_CSM_DIR_F(self.db.dname)
				dname=_util.realpath(dname)
				if not os.path.exists(dname):
					print("ディレクトリがありません",file=sys.stderr)
				random_=args["-r"] or args["--random"]
				cards=filter(lambda card:from_<=util.to_datetime(card.date)<until,self.db.search(memo,tags))
				if comment:
					cards=filter(lambda card:re.search(comment,card.comment(self.db.text)),cards)
				if not (args["--pn"] or args["--printNot"]):
					noTags.extend(ALL_NOT_L)
				if noTags:
					def filter_nt(cards):
						noTagIdxes=list(filter(lambda tag:tag,map(lambda tag:self.db.find(tag),noTags)))
						for card in cards:
							tagIdxes=self.db.cardToTags.get(card.id,[])
							if not any(map(lambda noTagIdx:noTagIdx in tagIdxes,noTagIdxes)):
								yield card
					cards=filter_nt(cards)
				if not random_:
					cards=sorted(cards,key=lambda card:card.date)
				fnames=map(lambda csm:os.path.join(dname,csm.fname),__data__.CSM.make(self.db.text,cards))
				fnames=filter(lambda fname:os.path.exists(fname),fnames)
				if random_:
					fnames=list(fnames)
					random.shuffle(fnames)
			fnames=filter(lambda fname:os.path.exists(fname),fnames)
			fnames=list(fnames)
			if not fnames:
				return
			n=len(fnames)//self.VIM_COUNT_OF_FILE + 1
			for i in range(n):
				if i!=0:
					output.write("You open next files... (.../n)")
					y_n=input().upper()
					if y_n == "N":
						break
				#sp.call(["vim","-Z",*fnames[i*self.VIM_COUNT_OF_FILE:i*self.VIM_COUNT_OF_FILE+self.VIM_COUNT_OF_FILE]])
				commands=[]
				port=self.environ.get(EnvKey.PORT)
				if port:
					commands.extend(("--cmd",f"let kyodaishiki_db_port={port}"))
				sp.call(["vim",*commands,\
				*fnames[i*self.VIM_COUNT_OF_FILE:i*self.VIM_COUNT_OF_FILE+self.VIM_COUNT_OF_FILE]])
			#sp.call(["vim",*fnames])
		elif query.command in Command.ALIAS:
			return self.alias(query.args,output)
		elif query.command in Command.DUMP:
			try:
				args=docopt.docopt(Docs.DUMP,query.args)
			except SystemExit as e:
				print(e)
				return
			if args["csv"]:
				tags=args["<tags>"].upper().split(",") if args["-t"] else []
				memo=args["<memo>"] or ""
				pMode=(args["<pMode>"] or "A").upper()
				P_TO_DATA={
					"M":"memo",
					"C":"comment",
					"T":"tags",
					"D":"date"
				}
				def _getPData(pMode):
					if "A" in pMode:
						pMode="MCTD"
					for mode in pMode:
						if mode in P_TO_DATA:
							yield P_TO_DATA[mode]
				def getPData(csm,pMode):
					for attr in _getPData(pMode):
						res=getattr(csm,attr)
						if type(res) in (tuple,list):
							res=",".join(res)
						yield res
				writer=csv.writer(output,lineterminator="\n")
				writer.writerow(_getPData(pMode))
				for card in self.db.search(memo,tags=tags):
					csm=__data__.CSM.makeOne(self.db.text,card)
					data=getPData(csm,pMode)
					writer.writerow(data)
					#data=map(lambda dat:dat.replace('"','\\"').replace('\n','\\n'),data)
					#data=map(lambda dat:f'"{dat}"',data)
			elif args["c"] or args["category"]:
				tags=args["<tags>"]
				if not tags:
					print("please set tag",file=output)
					return
				tag=tags.split(",")[0]
				args__=query.args[1:] if len(query.args) > 1 else []
				query=__shell__.Query(("dump",*args__))
				return category.DBShell(self.db,None,tag=tag).execQuery(query,output)
		elif query.command in Command.LINK:
			try:
				args=docopt.docopt(Docs.LINK,query.args)
			except SystemExit as e:
				print(e)
				return
			if args["s"] or args["search"]:
				searchArgs=util.arg_replace(args["<searchArgs>"])
				cards=self.search_card(searchArgs,output)
			else:
				memo=args["<memo>"] or ""
				tags=args["<tags>"].upper().split(",") if args["-t"] else []
				cards=self.db.search(memo=memo,tags=tags)
			pMode=args["<pMode>"].upper()+"M" if args["-p"] else "M"
			csms=__data__.CSM.make(self.db.text,cards)
			fnames=list(map(lambda csm:csm.fname,csms))
			sio=_pyio.StringIO()
			for card in self.db.search():
				comment=card.comment(self.db.text)
				if not any(map(lambda fname:fname in comment,fnames)):
					continue
				csm=__data__.CSM.makeOne(self.db.text,card)
				print("* "+csm.dump(pMode),file=sio)
				print("-"*50,file=sio)
			sio.seek(0)
			print(sio.read(),file=output)
		elif query.command in Command.COUNT:
			try:
				args=docopt.docopt(Docs.COUNT,query.args)
			except SystemExit as e:
				print(e)
				return
			if args["ln"] or args["link"]:
                                #find card that have many indexes.
                                searchArgs=list(util.arg_replace(args["<searchArgs>"]))
                                cards=self.search_card(searchArgs,output)
                                def _():
                                    for card in cards:
                                        comment=card.comment(self.db.text)
                                        n=len(re.findall("[0-9]+\.csm",comment))
                                        yield (n,card)
                                data=sorted(_(),key=lambda dat:dat[0])
                                for n,card in data:
                                    memo=card.memo(self.db.text)
                                    print(n,memo,file=output)
			elif args["c"] or args["col"]:
                            searchArgs=list(util.arg_replace(args["<searchArgs>"]))
                            print("ARGS",searchArgs)
                            cards=self.search_card(searchArgs,output)
                            for card in cards:
                                comment=card.comment(self.db.text)
                                res=list(util.Category.read(comment))
                                count=sum(map(lambda c:len(c.cols),res))
                                memo=card.memo(self.db.text)
                                print(memo,"->",count,file=output)
			elif args["w"] or args["word"]:
                            searchArgs=util.arg_replace(args["<searchArgs>"])
                            cards=self.search_card(searchArgs,output)
                            data={}
                            for csm in __data__.CSM.make(self.db.text,cards):
                                tags=",".join(csm.tags)
                                text=csm.memo+csm.comment+tags.upper()
                                words=getWords(text)
                                for word in words:
                                    if not data.get(word):
                                        data[word]=0
                                    data[word]+=1
                            data=sorted(data.items(),key=lambda item:item[1])
                            for word,n in data:
                                print(word,n,file=output)
			else:
                            searchArgs=util.arg_replace(args["<searchArgs>"])
                            cards=self.search_card(searchArgs,output)
                            reverse=args["-R"] or args["--reverse"]
                            from_=int(args["<from>"] or 0)
                            until=int(args["<until>"] or 10**32)
                            mode=(args["<mode>"] or "A").upper()
                            pMode=(args["<pMode>"] or "").upper()
                            def _dump(card,mode):
                                if "A" in mode:
                                    return _dump(card,"MCT")
                                res=""
                                if "M" in mode:
                                    res+=card.memo(self.db.text)
                                if "C" in mode:
                                    res+=card.comment(self.db.text)
                                if "T" in mode:
                                    res+=str(card.tags(self.db.text))
                                return res
                            def _():
                                for card in cards:
                                    count=len(_dump(card,mode))
                                    yield (count,card)
                            data=sorted(_(),key=lambda dat:dat[0],reverse=reverse)
                            sio=_pyio.StringIO()
                            for n,card in data:
                                if not from_ <= n < until:
                                    continue
                                memo=card.memo(self.db.text)
                                print(n,memo,file=sio)
                                if "F" in pMode:
                                    csm=__data__.CSM.makeOne(self.db.text,card)
                                    print("\t",csm.fname,file=sio)
                            sio.seek(0)
                            print(sio.read(),file=output)
		elif query.command in Command.HISTORY:
			try:
				args=docopt.docopt(Docs.HISTORY,query.args)
			except SystemExit as e:
				print(e)
				return
			if args["ls"]:
                            for query in self.query_history:
                                print(query,file=output)
			elif args["clear"]:
                            self.query_history.clear()
		elif query.command in Command.GREP:
                        try:
                            args=docopt.docopt(Docs.GREP,query.args)
                        except SystemExit as e:
                            print(e)
                            return
                        text=args["<text>"]
                        searchArgs=args["<searchArgs>"]
                        searchArgs=list(util.arg_replace(searchArgs))
                        cards=self.search_card(searchArgs,output)
                        for csm in __data__.CSM.make(self.db.text,cards):
                            for i,line in enumerate(csm.comment.split("\n")):
                                if re.search(text,line):
                                    print(f"* {csm.memo} : {csm.fname}\n=> L{i+1} : {line}",file=output)
                                    print("-"*50,file=output)
		elif query.command in Command.INDEX:
			try:
				args=docopt.docopt(Docs.INDEX,query.args)
			except SystemExit as e:
				print(e)
				return
			args__=args["<args>"]
			from . import index
			return index.DBShell(self.db).execQuery(\
                                __shell__.Query(args__),\
                                output
                        )
		elif query.command in Command.SET:
			try:
				args=docopt.docopt(Docs.SET,query.args)
			except SystemExit as e:
				print(e)
				return
			value=args["<value>"]
			if type(value) is not type(None):
				self.environ[args["<key>"].upper()]=args["<value>"]
			else:
				key=args["<key>"] if args["<key>"] else ""
				for envkey in self.environ:
					if re.match(key,envkey):
						output.write("{0} : {1}\n".format(envkey,self.environ[envkey]))
		elif query.command in Command.NUMBER:
			try:
				args=docopt.docopt(Docs.NUMBER,query.args)
			except SystemExit as e:
				print(e)
				return
			if args["s"] or args["search"]:
				searchArgs=args["<searchArgs>"]
				searchArgs=util.arg_replace(searchArgs)
				cards=self.search_card(searchArgs,output)
			else:
				memo=args["<memo>"] or ""
				tags=args["<tags>"].upper().split(",") if args["-t"] else []
				cards=self.db.search(memo,tags)
			print(len(list(cards)),file=output)
		elif query.command in self.aliasCommands:
			#query__=copy.copy(self.aliasCommands[query.command])
			#query__.extend(query.args)
			query__=self.aliasCommands[query.command]
			query__=__shell__.Query((*query__.data,*query.args))
			return self.execQuery(query__,output)
		else:
			return __shell__.DBShell.execQuery(self,query,output)
	def search_card(self,args,output):
		try:
			args=docopt.docopt(Docs.SEARCH_CARD,args)
		except SystemExit as e:
			print(e,args)
			return
		memo=args["<memo>"] if args["-m"] else ""
		if args["--mm"]:
			memo=addlowUp(memo,args["<lowUpMemo>"])
		if args["--em"]:
			memo=util.addMemo(memo,re.escape(args["<escapedMemo>"]))
		tags=args["<tags>"].upper().split(",") if args["-t"] else []
		comment=args["<comment>"] if args["-c"] else ""
		all_text=args["<all_text>"]
		from_=args["<from>"] if args["-F"] else "1900-01-01"
		from_=util.to_datetime(from_)
		until=args["<until>"] if args["-U"] else "3000-01-01"
		until=util.to_datetime(until)
		noTags=args["<noTags>"].upper().split(",") if args["--nt"] else []
		U=self.db.getU()
		#if not (args["--pn"] or args["--printNot"]) and noTags:
		printNot=args["--pn"] or args["--printNot"]
		if not printNot:
			noTags.extend(ALL_NOT_L)
			#noTags[-1]=noTags[-1]+"||"+NOT
		#noTags=self.db.getTagsRec(noTags,U)
		if args["-u"]:
			userid=args["<userid>"]
			tags.append(Attr(Attr.USERID)(userid))
		if args["-D"]:
			dbid=args["<dbid>"].upper()
			tags.append(Attr(Attr.DBID)(dbid))
		try:
			cards=filter(lambda card:from_<=util.to_datetime(card.date)<until,self.db.search(memo,tags))
		except Exception as e:
			print(e)
			return []
		regComment=re.compile(comment)
		data=""
		def getCards():
			for card in cards:
				tags=card.tags(self.db.text)
				if any(map(lambda tag:tag in tags,noTags)):
					continue
				elif comment and not re.search(regComment,card.comment(self.db.text)):
					continue
				if all_text:
					csm=__data__.CSM.makeOne(self.db.text,card)
					if not re.search(all_text,str(csm)):
						continue
				yield card
		return getCards()
	def search(self,args,output):
		try:
			args_=docopt.docopt(Docs.SEARCH,args)
		except SystemExit as e:
			print(e)
			return
		if args_["rec"]:
                    if args_["t"] or args_["bytag"]:
                        depth=int(args_["<depth>"] or 1)
                        searchArgs=args_["<searchArgs>"]
                        tag_n=int(args_["<tag_n>"] or 3)
                        searchArgs=util.arg_replace(searchArgs)
                        cards=self.search_card(searchArgs,output)
                        res=search_rec_by_tag(self.db,cards,depth=depth,tag_n=tag_n)
                        sio=_pyio.StringIO()
                        for depth in res:
                            data=res[depth]
                            for dat in data:
                                key=dat["key"]
                                for card in dat["cards"]:
                                    memo=card.memo(self.db.text)
                                    print(f"[{depth}]",f"[{key}]",memo,file=sio)
                        sio.seek(0)
                        print(sio.read(),file=output)
                        return
		elif args_["n"] or args_["not"]:
			#search (n|not) [(-t <tags>)] [(--nt <noTags>)] [(-m <memo>)] [(--mm <lowUpMemo>)] [(--em <escapedMemo>)] [(-c <comment>)] [(-F <from>)] [(-U <until>)] [(-u <userid>)] [(-D <dbid>)] [(-p <pMode>)] [(-r|--random)]
			args.pop(0)
			args__,_,_=util.partitionArgs(args,("-p","-r","--random","--al","--aslist"))
			if "-t" in args__:
				i=args__.index("-t")+1
				args__[i]+=","+ALL_NOT
			else:
				args__=("-t",ALL_NOT,*args__)
			cards=self.execQuery(__shell__.Query(("search_card",*args__,"--printNot")),output)
		else:
			args__,_,_=util.partitionArgs(args,("-p","-r","--random","--al","--aslist"))
			#cards=self.execQuery(__shell__.Query(("search_card",*args__)),output)
			cards=self.search_card(args__,output)
		pMode=args_["<pMode>"].upper()+"M" if args_["-p"] else "M"
		aslist=args_["--al"] or args_["--aslist"]
		if args_["-r"] or args_["--random"]:
			cards=list(cards)
			random.shuffle(cards)
		else:
			cards=sorted(cards,key=lambda card:card.date)
		data=""
		is_stdout=output is sys.stdout
		for csm in __data__.CSM.make(self.db.text,cards):
			if aslist:
				data+=csm.memo+"\n"
			else:
				data+="* "+csm.dump(pMode)+"\n"
				data+="-"*50+"\n"
		output.write(data)
	def start(self):
		if iscrayon(self.stdout):
			self.stdout.write(crayons.magenta("*** ")+crayons.blue(self.db.id)+crayons.magenta(" ***\n"))
		else:
			self.stdout.write("*** "+self.db.id+" ***\n")
		__shell__.BaseShell3.start(self)
		self.close()
	def close(self):
		cards=self.db.search(tags=[TMP_NOT])
		cardids=map(lambda card:card.id,cards)
		self.db.__removeTags__(cardids,[TMP_NOT])
		self.query_history.save()
		__shell__.DBShell.close(self)
		__shell__.BaseShell3.close(self)
		#csm_dname=DEFAULT_CSM_DIR_F.format(self.db.id)
		#if os.path.exists(csm_dname):
		#	shutil.rmtree(csm_dname)

class AuHSShell(__shell__.BaseShell3):
	PROMPT=">>"
	ALL_ENTER_BAT="se2_enter.bat"
	ALL_EXIT_BAT="se2_exit.bat"
	ALL_ALIAS_TXT="se2_alias.txt"
	SELECT_SHELL=DBShell
	def __init__(self,homeShell):
		super().__init__(prompt=self.PROMPT)
		self.homeDB=homeShell.home
		self.environ={}
	def select(self,query,output,shell_class=None):
		if shell_class is None:
		    shell_class=self.SELECT_SHELL
		dbids=list(self.homeDB.getDBIDs(query.command))
		if not dbids:
			return False
		dbid=dbids[0].upper()
		db=self.homeDB.select(dbid)
		if not db:
			output.write(dbid.lower()+" doesn't exist.\n")
			return False
		expander=util.Expander(self.homeDB,dbid)
		environ={
			**self.environ
		}
		if db.port and db.opened:
			environ[EnvKey.PORT]=db.port
		shell=shell_class(db,expander,environ=environ)
		all_enter_bat=os.path.join(self.homeDB.dname,self.ALL_ENTER_BAT)
		all_exit_bat=os.path.join(self.homeDB.dname,self.ALL_EXIT_BAT)
		all_alias=os.path.join(self.homeDB.dname,self.ALL_ALIAS_TXT)
		_util.touch(all_enter_bat)
		_util.touch(all_exit_bat)
		_util.touch(all_alias)
		shell.execAliasf(all_alias,self.null)
		if query.args:
			shell.execQuery(__shell__.Query(query.args),output)
		else:
			shell.beginf(all_enter_bat)
			shell.start()
			shell.beginf(all_exit_bat)
	def execQuery(self,query,output):
		return self.select(query,output)
	def start(self):
		self.stdout.write("Don't find dbid.\n")
