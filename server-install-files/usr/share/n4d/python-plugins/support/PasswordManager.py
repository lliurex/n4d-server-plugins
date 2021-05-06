# -*- coding: utf-8 -*-

import os
import shutil
import json
import codecs

import sqlite3

class PasswordManager:
	
	PASSWORD_FILE="/net/server-sync/var/lib/n4d/n4d.json"
	LOG_PATH="/net/server-sync/var/lib/n4d"
	
	def __init__(self):
			
		self.users={}
		
		if not os.path.exists(PasswordManager.LOG_PATH):
			os.makedirs(PasswordManager.LOG_PATH)
		
		if not os.path.exists("/lib/systemd/system/net-server\\x2dsync.mount"):
			
			self.load_password_file()
			
	#def init

	
	def sqlite_to_json(self,force_write=False):
		
		try:
			conn = sqlite3.connect("/net/server-sync/var/lib/n4d/n4d.sqlite")
			cursor = conn.cursor()
			cursor.execute('select cn,sn,uid,passwd from password')
			result = cursor.fetchall()
			conn.close()
			
			self.users={}
			for user in result :
				self.users[user[2]]={}
				try:
					self.users[user[2]]["cn"] = user[0].encode('utf-8')
				except:
					self.users[user[2]]["cn"] = user[2]
				try:
					self.users[user[2]]["sn"] = user[1].encode('utf-8')
				except:
					self.users[user[2]]["sn"] = user[2]
				try:
					self.users[user[2]]["passwd"] = user[3]
				except:
					self.users[user[2]]["passwd"] = "#! UNKNOWN PASSWORD !#"	
			
			if force_write:
				self.write_file()
			
			return True
		except Exception as e:
			print(e)
			
			return False
		
	#def sqlite_to_json
	
		
	def load_password_file(self, f=None):

		self.users={}
		if f==None:
			f=PasswordManager.PASSWORD_FILE
			
		if not os.path.exists(f):
			return False
		
		try:
			pfile=open(f,"r")
			self.users=json.load(pfile)
			pfile.close()
							
		except Exception as e:
			print("[PasswordManager] Error reading file: %s"%e)
				
	#def load_json
	
	
	def write_file(self,f=None):
		
		if f==None:
			f=PasswordManager.PASSWORD_FILE
		
		set_perms=False
		if not os.path.exists(f):
			set_perms=True
		
		for user in self.users:
			if type(self.users[user]["cn"])!=str:
				self.users[user]["cn"]=self.users[user]["cn"].decode("utf-8")
			if type(self.users[user]["sn"])!=str:
				self.users[user]["sn"]=self.users[user]["sn"].decode("utf-8")
		
		print(self.users)
		data=json.dumps(self.users,indent=4,ensure_ascii=False)
		output_file=open(f,"w")
		output_file.write(data)
		output_file.close()
		
		if set_perms:
			prevmask=os.umask(0)
			os.chmod(f,0o640)
			os.umask(prevmask)
		
	#def write_file

	
	def add_password(self,user_name,cn,sn,password):
		
		if user_name not in self.users:
			self.users[user_name]={}
		
		'''
		if type(cn)==str:
			cn=cn.encode("utf-8")
		if type(sn)==str:
			sn=sn.encode("utf-8")
		'''
	
		self.users[user_name]["cn"]=cn
		self.users[user_name]["sn"]=sn
		self.users[user_name]["passwd"]=password
		
		self.write_file()
		
	#def add_password
	
	
	def remove_password(self,user_name):
		
		if user_name in self.users:
			self.users.pop(user_name)
			
		return True
	
	#def remove_password
	
	
	def get_passwords(self):
		
		pwd_list = []
		for user in self.users :
			
			a = {}
			try:
				a['cn'] = self.users[user]["cn"].encode("UTF-8")
			except:
				print("[PasswordManager] Error reading user cn %s."%user)
				a['cn'] = user
				
			try:
				a['sn'] = self.users[user]["sn"].encode("UTF-8")
			except:
				print("[PasswordManager] Error reading user sn %s."%user)
				a['sn'] =user
			
			a['uid'] = user
			try:
				a['passwd'] = self.users[user]["passwd"]
			except:
				print("[PasswordManager] Error reading user passwd %s."%user)
				a['passwd'] = "#! UNKNOWN PASSWORD !#"
				
			pwd_list.append(a)
			
			

		return pwd_list
		
	#def get_passwords
	
	
	def is_user_in_database(self,uid):
		
		for user in self.users:
			return True
			
		return False
		
	#def is_user_in_database
	
	
	def set_externally_modified(self,uid):
		
		if self.is_user_in_database(uid):
			self.add_password(uid,self.users[uid]["cn"],self.users[uid]["sn"],"#! CHANGED MANUALLY !#")
			
	#def set_externally_modified	
	
	
#class PasswordManager

if __name__=="__main__":
	
	pm=PasswordManager()
	

