# -*- coding: utf-8 -*-

import os
import os.path
import base64
import shutil
import pwd
import tempfile


NET_FOLDER="/net/server-sync/home/.lliurex-harvester/"



class TeacherShareManager:

	def __init__(self):
		
		self.paths={}
		
	#def __init__
	
	def remove_path(self,uid):
		if uid in self.paths:
			path,name,ip,port,tmppath=self.paths[uid]
			self.paths.pop(uid)
			'''
			try:
				shutil.rmtree(tmp+"."+uid+"_"+name)
			except Exception as e:
				print e
			'''
					
		return True
		
	#def remove_path
	
	def add_path(self,user,path,name,ip,port):
				
		tmp=tempfile.mkdtemp()
		path=path.encode("utf8")
		name=name.encode("utf8")
		
		dir=tmp+"/."+user+"_"+name
		
		if user in self.paths:
			try:
				p,n,i,port=self.paths[user]
				shutil.rmtree(tmp+"/."+user+"_"+n)
			except Exception as e:
				# folder might not exist
				print e
				
		for item in os.listdir(tmp):
			if item.find("/."+user)==0:
				shutil.rmtree(tmp+item)
				
			
		prevmask = os.umask(0)
		
		try:
			self.paths[user]=(dir,name,ip,port)
			os.mkdir(dir)
			teacher_uid=pwd.getpwnam(user)[2]
			teacher_gid=pwd.getpwnam(user)[3]			
			os.chown(tmp,teacher_uid,teacher_gid)
			os.chown(dir,teacher_uid,teacher_gid)
			os.chmod(tmp,0703)
			os.chmod(dir,0703)
			os.umask(prevmask)		
			return True
			
		except Exception as e:
			
			print e
			
			if user in self.paths:
				self.paths.pop(uid)
				
			os.umask(prevmask)
			
			return False
		
	#def add_user
	
	def is_configured(self,user,orig_path):
		
		if user in self.paths:
			
			path,ip,name,port=self.paths[user]
			if orig_path[len(orig_path)-1]!="/":
				orig_path+="/"
			if path==orig_path:
				return True
			else:
				return False			
		else:
			return False
		
	#def is_configured
	
	def clear_paths(self):
		
		self.paths={}
		
		return True
		
	#def clear_paths
	
	def get_paths(self):
		
		return self.paths
		
	#def get_paths


#class TeacherShareManager
 
