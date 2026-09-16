from _kyodaishiki import __shell__
from _kyodaishiki import _util
from _kyodaishiki import __db__
from _kyodaishiki import __data__
from _kyodaishiki import __index__
from . import select2
from . import util
import os
import sys
import random
import _pyio
import docopt
import datetime
import re
from googletrans import Translator

TAG="REVIEW"

COMMENT_SEQ="\n-\n"

class Attr(util.Attr):
	POINT="POINT"
	SORT_OF="SORT_OF"
	PRICE="PRICE"

class ReviewCard(__index__.Card):
	def __init__(self,memoIdx=__index__.Index(),commentIdx=__index__.Index(),tagIdxes=list(),date=str(datetime.datetime.now()).split(".")[0]):
		super().__init__(memoIdx,commentIdx,tagIdxes,date)
		self.__point=-1
		self.__price=-1
	def point(self,text):
		if self.__point < 0:
			self.__point=getPoint(self.tags(text))
		return self.__point
	def price(self,text):
		if self.__price < 0:
			self.__price=int(Attr.get(self.tags(text),Attr.PRICE,[0])[0])
		return self.__price
	@staticmethod
	def make(cards):
		return map(lambda card:ReviewCard(card.memoIdx,card.commentIdx,card.tagIdxes,card.date),cards)

def write_shell(output=sys.stdout):
	output.write("Name:")
	name=input()
	output.write("Point:")
	point=int(input())
	output.write("Price:")
	price=int(input())
	output.write("Comment(one liner):")
	comment=input()
	sortofs=list(_util.inputUntilSeq("Sort of:",output=output))
	return __data__.CSM(name,comment,(*map(lambda sortof:Attr(Attr.SORT_OF)(sortof),sortofs),Attr(Attr.POINT)(point),Attr(Attr.PRICE)(price),TAG),str(datetime.datetime.now()).split(".",1)[0])

def getPoint(tags):
	return int(Attr.get(tags,Attr.POINT,[0])[0])

def __search__(db,name="",sortsof=[],fromP=0,untilP=100,tags=[]):
	tags=(*tags,*map(lambda sortof:Attr(Attr.SORT_OF)(sortof),sortsof)) if sortsof else tags
	for card in ReviewCard.make(db.search(name,tags=tags)):
		if fromP <= card.point(db.text) <= untilP:
			yield card
def search(db,name="",sortsof=[],fromP=0,untilP=100):
	return __search__(db,name,sortsof,fromP,untilP,[TAG])
	


class Docs:
    MAKE="""
    Usage:
        make (w|wl|wordlist) <wordlistpath> [(-T <title>)] [(-t <tags>)] [(-u <url>)] [(--lang-src <lang_src>)] [(--lang-dst <lang_dst>)]
    """
    HELP="""
        make
    """
class Command(select2.Command):
    MAKE=("M","MAKE")

class DBShell(select2.DBShell):
	def execQuery(self,query,output):
		if query.command in  Command.HELP:
			output.write(Docs.HELP+"\n")
			if query.args and query.args[0] in ("-a","--all"):
				return super().execQuery(query,output)
		elif query.command in  Command.MAKE:
                    try:
                        args=docopt.docopt(Docs.MAKE,query.args)
                    except SystemExit as e:
                        print(e)
                        return
                    if args["w"] or args["wl"] or args["wordlist"]:
                        _fname=args["<wordlistpath>"]
                        lang_src=args["<lang_src>"] or "en"
                        lang_dst=args["<lang_dst>"] or "ja"
                        tags=args["<tags>"].split(",") if args["-t"] else []
                        fname=_util.realpath(_fname)
                        with open(fname,"r") as f:
                            words=list(map(lambda line:line.strip(),f.readlines()))
                        words_sep="|"
                        words_text=words_sep.join(words)
                        trans=Translator()
                        res=trans.translate(words_text,src=lang_src,dest=lang_dst)
                        dst_words=res.text.split(words_sep)
                        print(dst_words)

                        memo=args["<title>"] if args["-t"] else "{0}:{1}".format(_fname,str(hash(str(words))))
                        comment=""
                        if args["-u"]:
                            comment+=f"\"{args['<url>']}\n"
                        cols=map(lambda a,b:f"{a}\t: {b}",words,dst_words)
                        c=util.Category("WORDS",cols=cols)
                        comment+=str(c)
                        tags=("IS_WORDLIST",*tags)
                        self.db.append(memo,comment,tags,str(datetime.datetime.now()))
                        print("Appended",memo,file=output)
		else:
			return super().execQuery(query,output)

class DUShell(__shell__.BaseShell):
	PROMPT=">>"
	def __init__(self,dushell):
		super().__init__(prompt=self.PROMPT)
		self.DBShell=DBShell
		self.homeDB=dushell.homeDB
	def execQuery(self,query,output):
		dbid=query.command.upper()
		if not dbid:
			output.write("Select dbid.\n")
			return
		db=self.homeDB.select(dbid)
		if not db:
			output.write("Don't find {0}.\n".format(dbid.lower()))
			return
		alias_txt=os.path.join(self.homeDB.dname,select2.AuHSShell.ALL_ALIAS_TXT)
		try:
			shell=self.DBShell(db)
			shell.execAliasf(alias_txt,_pyio.StringIO())
			shell.start()
		except Exception as e:
			output.write(str(e)+"\n")
	def start(self):
		return self.execQuery(__shell__.Query(),self.stdout)


