import requests
from bs4 import BeautifulSoup as bs
import time
import re
import docopt
import os
import urllib
import datetime
import sys
import urllib.parse as up
from collections import *
from _kyodaishiki import __db__
from _kyodaishiki import __utils__
from _kyodaishiki import __data__
from _kyodaishiki import __index__
from _kyodaishiki import __shell__
from . import mecab
from . import util
from . import select2


JA_HOST="ja.wikipedia.org"
JA_URL_F="https://"+JA_HOST+"/{0}"

REG_WIKIPEDIA=re.compile("https*://[^/]*wikipedia\..*")

DEFAULT_WIKIPEDIA_CSM_DIR=__utils__.realpath("%USERPROFILE%\\DeskTop\\wikipediaCSM")

ICHIRAN=b'\xe4\xb8\x80\xe8\xa6\xa7'.decode()
NOICHIRAN=b'\xe3\x81\xae'.decode()+ICHIRAN

DEF_URL_FILTER="https?://ja.wikipedia.org/wiki/.+"

class Section:
	def __init__(self,id_=None,data=[]):
		self.id=id_
		self.data=data
	def __bool__(self):
		return bool(self.id)
	def __str__(self):
		return str(util.Category(self.id,map(lambda dat:dat.text,self.data)))

def getSections(soup):
	data=soup.select_one(".mw-parser-output")
	data=list(data.find_all())
	lenData=len(data)
	id_=""
	e_data=[]
	i=0
	while i < lenData:
		element=data[i]
		#if type(element) is not bs4.element.Tag:
		#	continue
		class_ = element.get("class")
		if class_ and "mw-headline" in class_:
			if id_:
				yield Section(id_,e_data)
			e_data=[]
			id_=element.get("id")
		else:
			e_data.append(element)
		i+=1

def getSectionsByUrl(url):
	text=requests.get(url)
	soup=bs(text,"html.parser")
	return getSections(soup)

def getListInSection(section):
#section = [<element>,...]
	def getList(elements):
		for element in elements:
			for l in element.select("li"):
				yield l
	return reduce(lambda a,b:a+b,(*map(lambda e:e.select("li"),section.data),[]))

def __getList__(soup):
	for section in getSections(soup):
		yield (section.id,getListInSection(section))
def getList(soup):
	return dict(__getList__(soup))


def islist(title):
	return ICHIRAN in title	#"ichiran" in title

class Category(util.Category):
	def __init__(self,title="",url="",childs=[]):
		super().__init__(title=title,childs=childs)
		self.url=url

def __getCategoryInSection__(section,depth=3):
	if depth<=0:
		return
	if not islist(title):
		return
	url=""
	childs=[]
	for l in getListInSection(section):
		a=l.find("a")
		if not a:
			continue
		title=a.text
		if islist(title):
			href=a.get("href")
			if not href:
				continue
			href=urllib.parse.join(url,a.get("href"))
			cs=[]
			for section in getSectionsByUrl(url):
				cs.append(getCategoryInSection(section,depth-1))
			childs.append(util.Category(title,href,cs))
		else:
			childs.append(util.Category(title))
	return Category(section.id,childs=childs)
def getCategory(soup,n=3):
	cs=map(lambda section:getCategoryInSection(section),getSections(soup))
	title=soup.find(id="firstHeading")
	return Category(title,JA_URL_F.format(title),cs)


class Attr(util.Attr):
	TITLE="TITLE"
	N="N"
	to_format=lambda attr:attr+":{0}"

attr_to_format=Attr.to_format

def isWikipedia(url):
	if not url:
		return False
	return re.match(REG_WIKIPEDIA,url) or url[0]=="/"

def islist(title):
	return ICHIRAN in title or NOICHIRAN in title


class _Article:
	WIKIPEDIA="Wikipedia"
	NORMAL=1
	LIST=2
	def __init__(self,text):
		self.__text=text
		self.__soup=None
		self.__title=None
		self.__mode=None
	@property
	def text(self):
		return self.__text
	@property
	def soup(self):
		if not self.__soup:
			self.__soup=bs(self.text,"html.parser")
		return self.__soup
	@property
	def title(self):
		if not self.__title:
			self.__title=self.getTitle(self.soup)
		return self.__title
	@property
	def mode(self):
		if not self.__mode:
			self.__mode=self.getMode(self.title)
		return self.__mode
	def __hash__(self):
		return hash(self.title)
	@property
	def tot_title(self):
		return self.getTOTTitle(self.title)
	def childs(self):
		URL=f"https://{JA_HOST}"
		for a in self.soup.select("a"):
			href=a.get("href")
			if not href:
				continue
			href=up.urljoin(URL,href)
			if href and isWikipedia(href):
				yield Article(href)
	@staticmethod
	def getMode(title):
		if not title:
			return _Article.NORMAL
		elif "Category:" in title:
			return _Article.LIST
		return _Article.NORMAL
	def dumpCSM(self):
		tags=[Article.WIKIPEDIA,Attr(Attr.TITLE)(self.title)]
		attr_n_f=Attr(Attr.N)
		titleInMemo=" ({0})".format(self.title)
		
		i=0
		for text in map(lambda p:p.text,self.soup.select("p")):
			for sentence in mecab.Mecab.getDataAsSentence(text):
				if sentence:
					yield __db__.CSM(sentence,tags=tags+attr_n_f.format(i))
					i+=1

	@staticmethod
	def getTitle(soup):
		for meta in soup.find_all("meta"):
			if meta.get("property")=="og:title":
				return meta.get("content").split("-")[0].rstrip()

class Article(_Article):
	def __init__(self,url):
		self.url=url
		self.__text=None
		super().__init__(None)
	@property
	def text(self):
		if not self.__text:
			res=requests.get(self.url)
			self.__text=res.text
		return self.__text

		

class _List(_Article):
	@staticmethod
	def cleanTag(tag):
		return re.sub("^Category:","",tag)
	def dumpTOT(self):
		if not self.title:
			return None
		name=self.getTOTTitle(self.title)
		tags=[]
		for li in self.soup.select("li"):
			if li.get("class") or li.get("id"):#if li dont have class and id , it's normal data
				continue
			a=li.find("a")
			if a and a.get("title"):
				title=a.get("title")
				title=_List.cleanTag(title)
				tags.append(title)
		return __data__.TOT.make2(name,tags)
	@staticmethod
	def getTOTTitle(title):
		def resMeishi(s):
			for data in mecab.Mecab(s)():
				if len(data) > 1:
					if b"\xe5\x90\x8d\xe8\xa9\x9e".decode() in data[1][0]:
						yield data
		def resX(s):
			for data in resMeishi(s):
				if data[0] != ICHIRAN:
					yield data[0]
		title=_List.cleanTag(title)
		return __data__.Logic.AND.join(resX(title))

class List(_List):
	def __init__(self,url):
		self.url=url
		res=requests.get(url)
		super().__init__(res.text)

class Card(__index__.Card):
	def __init__(self,memoIdx=__index__.Index(),commentIdx=__index__.Index(),tagIdxes=[],date=str(datetime.datetime.now())):
		super().__init__(memoIdx,commentIdx,tagIdxes,date)
		self.__attr_data={}
		self.__n=-1
		self.__title=""
	def attr_data(self,text):
		if not self.__attr_data:
			self.__attr_data=Attr.parse(self.tags(text))
		return self.__attr_data
	def n(self,text):
		if self.__n < 0:
			ns=self.attr_data(text).get(Attr.N,[])
			self.__n=int(ns[0]) if ns else -1
		return self.__n
	def title(self,text):
		if not self.__title:
			self.__title=self.attr_data(text).get(Attr.TITLE,"")
		return self.__title
	@staticmethod
	def make(cards):
		for card in cards:
			yield Card(card.memoIdx,card.commentIdx,card.tagIdxes,card.date)


def __concatAsTextOne__(db,tag,from_=0,until_=10**32):
	cards=db.search(tags=[tag])
	cards=Card.make(cards)
	cards=sorted(cards,key=lambda card:card.n(db.text))
	def getSentences(cards__):
		for card in cards__:
			if from_ <= card.n(self.text) < until_:
				yield card.memo(db.text)
	return "".join(getSentences(cards))
def concatAsTextOne(db,title,from_=0,until_=10**32):
	return __concatAsTextOne__(db,Attr(Attr.TITLE)(title),from_,until)

def concatAsText(db,title=".*"):
	attr_title=Attr(Attr.TITLE)(title)
	for tag in filter(lambda tag:re.search("^"+attr_title+"$",tag),db.getTags()):
		yield __concatAsTextOne__(db,tag)

def crawl(url,n=10,depth=3,log=sys.stderr):
	frontiers=deque([(Article(url),0)])
	explored=list()
	while frontiers:
		now,current_depth=frontiers.popleft()
		print("NOW CRAWLING",now.url,file=log)
		if current_depth >= depth:
			break
		if now not in explored:
			childs=now.childs() or []
			frontiers.extend(map(lambda child:(child,current_depth+1),childs))
			yield now
			explored.append(hash(now))

def getCSM(url,n=10):
	for a in crawl(url,n):
		for csm in a.dumpCSM():
			yield csm
def getTOT(url,n=10,depth=3,url_filter=DEF_URL_FILTER):
	for a in crawl(url,n,depth=depth):
		if not re.match(url_filter+"$",a.url):
			continue
		if a.mode==Article.LIST:
			a=_List(a.text)
			yield a.dumpTOT()




class Docs:
	class DB:
		TITLE="""
		Usage:
			title [<title>]
		"""
		APPEND="""
		Usage:
			append tot <title> [(--dp <depth>)] [(--uf <url_filter>)] [(-O|--override)] 
			append <title>
			append (cr|crawl) <title> [(-n <number>)]
			append list <title>
		"""
		HELP="""
	title [<title>]
	append <title>
	append list <title>
		"""
HELP="""
$ append <dbid> <title>
$ select <dbid>
"""

class Command(__utils__.Command):
	TITLE=("TI","TITLE")
	APPEND=("A","APPEND")

class DBShell(select2.DBShell):
	DEF_CRAWL_N=10
	def execQuery(self,query,output):
		if query.command in __utils__.Command.QUIT:
			raise SystemExit
		elif query.command in __utils__.Command.HELP:
			output.write(Docs.DB.HELP+"\n")
		elif query.command in Command.TITLE:
			title=re.compile("TITLE:{0}".format(query.args[0])) if query.args else "TITLE:.*"
			for tag in self.db.getTags():
				if re.match(title,tag):
					tag=tag.replace("TITLE:","")
					output.write(tag)
		elif query.command in Command.APPEND:
			try:
				args=docopt.docopt(Docs.DB.APPEND,query.args)
			except SystemExit as e:
				print(e)
				return
			if args["list"]:
				url=os.path.join("https://wikipedia.co.jp",title)
			elif args["tot"]:
				title=args["<title>"]
				url_filter=args["<url_filter>"] or DEF_URL_FILTER
				#titles=(title,f"wiki/Category:{title}")
				titles=[f"wiki/Category:{title}"]
				override=args["-O"] or args["--override"]
				depth=int(args["<depth>"] or 1)
				for title__ in titles:
					url=JA_URL_F.format(title__)
					try:
						for tot in getTOT(url,depth=depth,url_filter=url_filter):
							try:
								print(tot,file=sys.stderr)
								if not tot:
									continue
								self.db.appendTOT(tot.name,tot.childs,override=override)
							except Exception as e:
								print(e,file=sys.stderr)
							except KeyboardInterrupt:
								pass
							else:
								print("Appended",tot.name,file=output)
					except KeyboardInterrupt:
						pass
			elif args["cr"] or args["crawl"]:
				try:
					title=args["<title>"]
					number=int(args["<number>"]) if args["-n"] else self.DEF_CRAWL_N
					url=JA_URL_F.format(title)
					for article in crawl(url):
						for csm in article.dumpCSM():
							self.db.appendCSM(csm)
				except Exception as e:
					print(e)
			else:
				title=args["<title>"]
				url=os.path.join("https://wikipedia.co.jp",title)
				article=Article(url)
				for csm in article.dumpCSM():
					self.db.appendCSM(csm)
		else:
			super().execQuery(query,output)
	def start(self):
		self.stdout.write("*** welcome to wikipedia ***\n")
		return super().start()
	

def execQuery(homeDB,query):
	if not query:
		return
	command=query[0].upper()
	args=query[1:] if len(query)>1 else list()
	if command in __utils__.Command.QUIT:
		raise SystemExit
	if command in __utils__.Command.HELP:
		print(HELP)
	elif command in __utils__.Command.APPEND:
		try:
			args=docopt.docopt(__utils__.Docs.Wikipedia.APPEND,args)
		except SystemExit as e:
			print(e)
			return
		except Exception as e:
			print(e)
			return
		title=args["<title>"]
		dbid=args["<dbid>"]
		db=homeDB.select(dbid)
		if not db:
			homeDB.append(dbid,["wikipedia"])
			db=homeDB.select(dbid)
		DBShell(db).execQuery(query,output)
	elif command in __utils__.Command.DB.SELECT:
		if not args:
			print("	select <dbid>")
			return
		dbids=list(__db__.getDBIDs(homeDB,args[0].upper()))
		if not dbids:
			print("Don't find.")
			return
		dbid=dbids[0]
		db=homeDB.select(dbid)
		if not db:
			print("Don't find",dbid,".")
		shell=DBShell(db)
#exec alias.txt of select2 in homeDB
		all_alias=os.path.join(homeDB.dname,select2.AuHSShell.ALL_ALIAS_TXT)
		shell.execAliasf(all_alias,shell.null)
		return shell.start()

class SiteShell(__shell__.BaseShell):
	def __init__(self,homeDB):
		self.homeDB=homeDB
		super().__init__()
	def execQuery(self,query,output):
		return execQuery(self.homeDB,query.data)
	def start(self):
		self.stdout.write("*** welcome to wikipedia ***\n")
		return super().start()

