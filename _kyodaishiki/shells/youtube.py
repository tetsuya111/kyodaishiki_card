from . import util
from . import select2
from . import util
from _kyodaishiki import __utils__
from _kyodaishiki import __shell__
from _kyodaishiki import __db__

import re
import os
import docopt

class Attr(util.Attr):
	CHANNEL_ID="CHANNEL_ID"

def getChannelID(url):
	#https://www.youtube.com/channel/UCrWMK-B92Il4NEo0GvJk4WQ/videos
	a=re.search("channel/(?P<id>[^/]+)/",url)
	if a:
		return a.group("id")
	return None

def write():
	channel_url=input("Channel URL (or ID) : ")
	chid=getChannelID(channel_url) or channel_url
	csm=__shell__.Shell.write()
	csm.tags=(*csm.tags,Attr(Attr.CHANNEL_ID).format(chid))
	return csm


class Docs:
	class DB:
		WRITE="""
		Usage:
			write (yt|youtube)
			write tot
			write
		"""
	class Home:
		HELP="""
	select
		"""

class Command(util.Command):
	WRITE=("W","WRITE")


class DBShell(select2.DBShell):
	def _execQuery(self,query,output):
		if query.command in Command.WRITE:
			args=docopt.docopt(Docs.DB.WRITE,query.args)
			if args["yt"] or args["youtube"]:
				csm=write()
				self.db.appendCSM(csm)
			else:
				return super().execQuery(query,output)
		else:
			return super().execQuery(query,output)
	def execQuery(self,query,output):
		try:
			return self._execQuery(query,output)
		except Exception as e:
			print(e)
		except SystemExit as e:
			print(e)
		except KeyboardInterrupt:
			pass

class SiteShell(__shell__.BaseShell):
	def __init__(self,homeDB):
		self.homeDB=homeDB
		super().__init__()
	def execQuery(self,query,output):
		if query.command in Command.HELP:
			print(Docs.Home.HELP,file=output)
		elif query.command in __utils__.Command.DB.SELECT:
			if not query.args:
				print("	select <dbid>")
				return
			dbids=list(__db__.getDBIDs(self.homeDB,query.args[0].upper()))
			if not dbids:
				print("Don't find.")
				return
			dbid=dbids[0]
			db=self.homeDB.select(dbid)
			if not db:
				print("Don't find",dbid,".")
			shell=DBShell(db)
#exec alias.txt of select2 in homeDB
			all_alias=os.path.join(self.homeDB.dname,select2.AuHSShell.ALL_ALIAS_TXT)
			shell.execAliasf(all_alias,shell.null)
			return shell.start()
		else:
			return super().execQuery(query,output)
