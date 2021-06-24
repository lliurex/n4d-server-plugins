# -*- coding: utf-8 -*-

import os
import os.path
import base64
import shutil
import pwd
import tempfile

import n4d.responses


NET_FOLDER="/net/server-sync/home/.lliurex-harvester/"



class TeacherShareManager:

	ADD_PATH_ERROR=-10

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
					
		return n4d.responses.build_successful_call_response()
		
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
				print(e)
				
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
			os.chmod(tmp,0o703)
			os.chmod(dir,0o703)
			os.umask(prevmask)		
			return n4d.responses.build_successful_call_response()
			
		except Exception as e:
			
			print(e)
			
			if user in self.paths:
				self.paths.pop(uid)
				
			os.umask(prevmask)
			
			return n4d.responses.build_failed_call_response(ADD_PATH_ERROR,str(e))
		
	#def add_user
	
	def is_configured(self,user,orig_path):
		
		if user in self.paths:
			
			path,ip,name,port=self.paths[user]
			if orig_path[len(orig_path)-1]!="/":
				orig_path+="/"
			if path==orig_path:
				return n4d.responses.build_successful_call_response(True)
			else:
				return n4d.responses.build_successful_call_response(False)
		else:
			return n4d.responses.build_successful_call_response(False)
		
	#def is_configured
	
	def clear_paths(self):
		
		self.paths={}
		
		return n4d.responses.build_successful_call_response(True)
		
	#def clear_paths
	
	def get_paths(self):
		
		return n4d.responses.build_successful_call_response(self.paths)
		
	#def get_paths


#class TeacherShareManager
 
