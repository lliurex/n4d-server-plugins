# -*- coding: utf-8 -*-

import os
import shutil
import pwd
import tempfile

import n4d.responses


class TeacherShareManager:

	ADD_PATH_ERROR=-10

	def __init__(self):
		
		self.paths={}
		
	#def __init__
	
	def remove_path(self,user):
		
		if user in self.paths:
			self.paths.pop(user)

		return n4d.responses.build_successful_call_response()
		
	#def remove_path
	
	def add_path(self,user,path,name,ip,port=None):
				
		#path=path.encode("utf8")
		#name=name.encode("utf8")
		
		try:
			if ip=="127.0.0.1":
				ip="server"
			self.paths[user]=(path,name,ip,port)
			return n4d.responses.build_successful_call_response()
			
		except Exception as e:
			
			print(e)
			if user in self.paths:
				self.paths.pop(uid)
				
			os.umask(prevmask)
			return n4d.responses.build_failed_call_response(ADD_PATH_ERROR,str(e))
		
	#def add_path
	
	def is_configured(self,user,orig_path):
		
		if user in self.paths:
			
			path,name,ip,port=self.paths[user]
			orig_path=orig_path.rstrip("/")
			path=path.rstrip("/")
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
 
