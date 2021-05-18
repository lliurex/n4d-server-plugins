# -*- coding: utf-8 -*-

import ldap
import subprocess
import base64,random,hashlib,string
import xml.etree
import xml.etree.ElementTree
import sys
import threading
import time
import passlib.hash
import grp


import unicodedata
import syslog

import os
import os.path

import n4d.server.core


base_home_dir="/home/"

LDAP_LOG="/var/log/n4d/ldap"

#uid=pepe,ou=Admins,ou=People,dc=ma5,dc=lliurex,dc=net
#lliurex


class GescenItem:
	
	def __init__(self):
		
		self.attributes={}
		
	#def init
	
	def print_me(self):
		
		print(self.attributes)
		
	#def print_me
	
#class GescenItem



class LdapUser:
	
	def __init__(self,properties):
		

		#list=['top', 'posixAccount', 'shadowAccount', 'person', 'sabayonProfileNameObject','x-lliurex-user']
		list=['top','person', 'sambaSamAccount','posixAccount','shadowAccount','x-lliurex-user']
		
		self.properties={}
		'''
		for key in properties:
			self.properties[key]=properties[key]
		'''
		self.properties=properties.copy()
		if type(self.properties["uid"])==bytes:
			self.properties["uid"]=self.properties["uid"].decode("utf-8")
		
		self.uid=self.properties["uid"]
		
		if "description" not in self.properties:
			if type(self.properties["cn"])==bytes:
				self.properties["cn"]=self.properties["cn"].decode("utf-8")
			if type(self.properties["sn"])==bytes:
				self.properties["sn"]=self.properties["sn"].decode("utf-8")
				
			self.properties["description"]=self.properties["cn"] +  " " + self.properties["sn"]
		
		
		
		self.properties["objectClass"]=list
		self.properties["loginShell"]="/bin/bash"
		self.properties["homeDirectory"]="/home/"+self.uid
		
		#SAMBA STUFF
		self.properties['sambaHomePath']="\\\\"+self.uid
		self.properties['sambaProfilePath']="\\\\profiles\\"+self.uid
		self.properties['sambaAcctFlags']='[U]'
		self.properties['gecos']=self.uid
		
		
		self.banned_list=['path','password','profile']
		

		
	def get_modlist(self,banned_list=None):
		
		list=[]
		
		if banned_list==None:
			banned_list=self.banned_list
		
		for key in self.properties:
			if key not in banned_list:
				list.append((key,self.properties[key]))

		return list
		
		
	#def get_modlist
		
		
		
		
	def print_me(self):
		
		
		print(self.properties)
		
	
#class LdapUSer



def strip_accents(s):
	return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))


def ldapmanager_connect(f):
	def wrap(*args,**kw):
		args[0].connect()
		return f(*args)
	return wrap
#def __try_connect__


class LdapGroup:
	
	def __init__(self,properties):
		
		self.attributes=[]
		#list=['top', 'posixGroup', 'lisGroup','x-lliurex-group']
		list=['top', 'posixGroup','x-lliurex-group','sambaGroupMapping']
		self.cn=properties["cn"]
		
		self.properties=properties
		
		if "description" not in self.properties:
			self.properties["description"]=self.cn
			description=self.cn
			
		self.properties["objectClass"]=list
		
		for key in self.properties:
			self.attributes.append((key,self.properties[key]))
			
		#self.attributes.append(('groupType','school_class'))
		
		

		
	#def __init__
	
	def print_me(self):
		
		print(self.properties)
	
#class LdapGroup



class LdapManager:


	RANDOM_PASSWORDS=0
	SAME_PASSWORD=1
	PASS_EQUALS_USER=2
	
	LDAP_SECRET1="/etc/lliurex-cap-secrets/ldap-master/ldap"
	LDAP_SECRET2="/etc/lliurex-secrets/passgen/ldap.secret"
	
	SAMBASID_FILE="/etc/n4d/sambaid"
	
	
	
	def __init__(self):
		
		self.core=n4d.server.core.Core.get_core()
		self.core.pprint("GOLEM.LDAPMANAGER","INIT")
		#self.llxvar=llxvar
		self.restore_connection=True
		self.reset_connection_variable()
		self.get_samba_id()
		
		try:
			self.connect()
			self.get_xid_counters()
			self.get_xgid_counter()
		except Exception as e:
			print(e)
			self.log("__init__",e)
			self.connection=False

	#def init

	def str_to_bytes(self,thing,skip=1):
		if isinstance(thing,list):
			thing_encoded = list()
			for other in thing:
				thing_encoded.append(self.str_to_bytes(other))
			return thing_encoded
		elif isinstance(thing,dict):
			thing_encoded = dict()
			for k,v in thing.items():
				thing_encoded[k]=self.str_to_bytes(v)
			return thing_encoded
		elif isinstance(thing,tuple):
			tmp_encoded=tuple()
			for t in thing:
				if skip > 0 and isinstance(t,str):
					skip -= 1
					tmp_encoded += (t,)
				else:
					tmp_encoded += (self.str_to_bytes(t),)
			return tmp_encoded
		elif isinstance(thing,str):
			return thing.encode('utf-8')
		else:
			return thing
	
	def llxvar(self,var_name):
		
		return self.core.get_variable(var_name)["return"]
		
	#def llxvar


	def reset_connection_variable(self):
		
		url=self.llxvar("MASTER_SERVER_IP")
		
		if url!=None:
			self.core.pprint("GOLEM.LDAPMANAGER","Starting connection thread...")
			t=threading.Thread(target=self._rcv_thread)
			t.daemon=True
			t.start()
		
	#def reset_connection_variable
	
	def _rcv_thread(self):
		
		while True:
		
			time.sleep(90)
			self.core.pprint("GOLEM.LDAPMANAGER","Restoring connection variable...")
			self.restore_connection=True
		
		
	#def _rcv_thread

	
	def log(self,function_name,exception,comment=None):
		
		try:
			f=open(LDAP_LOG,"a")
			f.write("* When calling " + function_name + " something happened...\n\t")
			f.write(str(exception))
			f.write("\n")
			if comment!=None:
				f.write("\tCoder Hint: " + str(comment))
				f.write("\n")
			f.close()
		except:
			pass
		
	#def log
	
	
	@ldapmanager_connect
	def get_xid_counters(self,uid="*"):
		
		result=self.ldap.search_s("ou=People,"+self.llxvar("LDAP_BASE_DN"),ldap.SCOPE_SUBTREE)
		
		self.xid_counters={}
		
		for item in result:
			path,properties_dic=item
			if b"x-lliurex-ou-properties" in  properties_dic['objectClass'] and "x-lliurex-xid-counter" in properties_dic:
				self.xid_counters[properties_dic['ou'][0].decode("utf-8")]=properties_dic['x-lliurex-xid-counter'][0].decode("utf-8")
	
		
		
	#def get_counter
	
	@ldapmanager_connect
	def get_xgid_counter(self):
		
		self.xgid_counter=None
		
		result=self.ldap.search_s("ou=Managed,ou=Groups,"+self.llxvar("LDAP_BASE_DN"),ldap.SCOPE_SUBTREE)
		for item in result:
			path,properties_dic=item
			if b"x-lliurex-ou-properties" in properties_dic["objectClass"] and "x-lliurex-xid-counter" in properties_dic:
				self.xgid_counter=properties_dic['x-lliurex-xid-counter'][0]
			
				
	#def get_xgid_counter
	
	@ldapmanager_connect
	def set_next_xid(self,ou):
		
		try:
			value=int(self.xid_counters[ou])
			value+=1
			mod=( ldap.MOD_REPLACE, "x-lliurex-xid-counter", str(value) )
			mod_list=[]
			mod_list.append(mod)
			path="ou="+ou+",ou=People," + self.llxvar("LDAP_BASE_DN")
			mod_list=self.str_to_bytes(mod_list)
			self.ldap.modify_s(path,mod_list)
			self.xid_counters[ou]=str(value)
			return [True,str(value)]
		except Exception as e:
			print(e)
			self.log("set_next_xid",e)
			return [False,e]
		
		
	#def set_next_xid_counter
	
	
	@ldapmanager_connect
	def set_xid(self,ou,value):
		
		mod=( ldap.MOD_REPLACE, "x-lliurex-xid-counter", str(value) )
		mod_list=[]
		mod_list.append(mod)
		path="ou="+ou+",ou=People," + self.llxvar("LDAP_BASE_DN")
		try:
			mod_list=self.str_to_bytes(mod_list)
			self.ldap.modify_s(path,mod_list)
			self.xid_counters[ou]=str(value)
			return True
		except Exception as e:
			#print e
			self.log("set_xid",e)
			return [False,e]
		
	#def set_xid_counter
	
	@ldapmanager_connect
	def set_next_xgid(self):
		
		try:
			value=int(self.xgid_counter)
			value+=1
		
			mod=( ldap.MOD_REPLACE, "x-lliurex-xid-counter", str(value) )
			mod_list=[]
			mod_list.append(mod)
			path="ou=Managed,ou=Groups," + self.llxvar("LDAP_BASE_DN")
			mod_list=self.str_to_bytes(mod_list)
			self.ldap.modify_s(path,mod_list)
			self.xgid_counter=str(value)
			return [True,str(value)]
		except Exception as e:
			print(e)
			self.log("set_next_xgid",e)
			return [False,e]
		
		
	#def set_next_xid_counter
	
	
	
	def get_samba_id(self):

		self.samba_id=None
		self.get_samba_id_first_run=False
		t=threading.Thread(target=self.get_samba_id_t)
		t.daemon=True
		t.start()
		
	#def get_samba_id
	
	
	def get_samba_id_t(self):
		
		for count in range(0,10):
		
			try:
				pprocess = subprocess.Popen(['net','getlocalsid'],stderr=subprocess.PIPE,stdout=subprocess.PIPE)
				sambaid = pprocess.communicate()[0].decode("utf-8")
				aux = sambaid.split(":")[1]
				self.samba_id = aux[1:len(aux)-1]
				self.get_samba_id_first_run=True
				self.core.pprint("GOLEM.LDAPMANAGER","Samba ID ready.")
				return True
			except Exception as e:
				self.core.pprint("GOLEM.LDAPMANAGER","Get Sanba ID failed: %s"%e)
				if count < 9:
					self.core.pprint("GOLEM.LDAPMANAGER","Retrying in 2s ...")
					time.sleep(2)

		self.get_samba_id_first_run=True
		return False
		
		
	#def get_samba_id_t
	
	
	
	def getsalt(self,chars = string.ascii_letters + string.digits,length=16):
		
		salt = ""
		for i in range(int(length)):
			salt += random.choice(chars)
		return salt
		
	#def getsalt

	
	def generate_random_ssha_password(self):
		password="".join(random.sample(string.ascii_letters+string.digits, 4))
		return self.generate_ssha_password(password),password
		
	#def generate_random_ssha_password
	
	def generate_ssha_password(self,password):
		
		salt=self.getsalt().encode("utf-8")
			
		
		return "{SSHA}" + base64.encodebytes(hashlib.sha1(password + salt).digest() + salt).decode('utf-8')
		#ret="{SSHA}" + base64.b64encode(hashlib.sha1(password.decode("utf-8") + salt).digest() + salt)
		#return ret
		
	#def generate_ssha_password	
	
	
	
	def generate_uid(self,name,surname):
		
		name_list=name.split(" ")
		surname_list=surname.split(" ")
		
		uid=""
		
		for i in range(0,len(name_list[0])):
			uid=uid+name_list[0][i]
			if len(uid)==3:
				break
				
		last_surname=len(surname_list)-1
		for i in range(0,len(surname_list[last_surname])):
			uid=uid+surname_list[last_surname][i]
			if len(uid)==6:
				break
			
		return uid
		
		
	#def generateUid
	
	
	def parseGescen(self,path):
		
		document=xml.etree.ElementTree.parse(path)
		root=document.getroot()

		alumnes=[]
		cursos=[]
		for node in root:
			if node.tag=="alumnes":
				alumnes=node.getchildren()
			if node.tag=="grups":
				cursos=node.getchildren()


		parsed_subjects=[]
		if len(cursos)>0:
			for curs in cursos:
				subject=GescenItem()
				items=curs.getchildren()
				for item in items:
					subject.attributes[item.tag]=item.text
					
				parsed_subjects.append(subject)
					


		parsed_students=[]
		if len(alumnes)>0:
			for alumne in alumnes:
				student=GescenItem()
				items=alumne.getchildren()
				for item in items:
					student.attributes[item.tag]=item.text
					
					
				parsed_students.append(student)

				
		if len(parsed_subjects)>0:
			for subject in parsed_subjects:
				codi=unicode(subject.attributes["codi"]).encode("ascii")
				nom=unicode(subject.attributes["nom"]).encode("utf-8")
				prop={}
				prop["cn"]=codi
				prop["description"]=nom
				prop["x-lliurex-grouptype"]="itaca"
				self.add_group(prop)
				
				
		if len(parsed_students)>0:
			for student in parsed_students:
				name_utf_encoded=False
				surname_utf_encoded=False
				
				name=strip_accents(unicode(student.attributes["nom"])).lower()
				name=unicode(name).encode("ascii")
				surname=strip_accents(unicode(student.attributes["cognoms"])).lower()
				surname=unicode(surname).encode("ascii")
				
				# // Generate uid
				
				uid=self.generate_uid(name,surname)
				'''
				uid=""
				count=0
				for char in name:
					if count<3:
						uid=uid+char
						count+=1
					else:
						break
				count=0
				for char in surname:
					if count<3:
						uid=uid+char
						count+=1
					else:
						break
				'''
				
				# // Generate uid
				
				
				group=unicode(student.attributes["grup"]).encode("ascii")

				
				if uid.find(" ")!=-1:
					uid=uid.replace(" ","")

				name=unicode(student.attributes["nom"]).encode("utf-8")
				surname=unicode(student.attributes["cognoms"]).encode("utf-8")
				
				
				properties={}
				properties["uid"]=uid
				properties["cn"]=name
				properties["sn"]=surname
				properties["password"]=uid
				
				generated_user=self.add_user(True,"Students",properties)
				#print self.add_to_group_type(group,generated_user["uid"])
		

	#def parseGescen
	
	
	def connect(self):
	
		if self.get_samba_id_first_run and self.samba_id==None:
			# Calling blocking call instead of thread
			self.get_samba_id_t()
		
		if self.restore_connection:
			self.restore_connection=False
			sys.stdout.write("[GOLEM.LDAPMANAGER] Connecting to ldap ... ")
			url=None
			remote=False
			try:
				url=self.llxvar("MASTER_SERVER_IP")
				if url!=None:
					url="ldap://"+url
					remote=True
			except Exception as e:
				print((e,""))
			
			do_it=True
			
			if not remote:
			
				try:
					#url=self.llxvar("CLIENT_LDAP_URI")
					url="ldaps://localhost"
					count=1
				except Exception as e:
					print((e,""))
					return None
					
			else:
				count=2
			
			for x in range(0,count):
			
				try:
				
					self.ldap=ldap.initialize(url)
					self.ldap.set_option(ldap.VERSION,ldap.VERSION3)
					
					if os.path.exists(LdapManager.LDAP_SECRET1):
						f=open(LdapManager.LDAP_SECRET1)
						lines=f.readlines()
						f.close()
						password=lines[0].replace("\n","")
					else:
						if os.path.exists(LdapManager.LDAP_SECRET2):
							f=open(LdapManager.LDAP_SECRET2)
							lines=f.readlines()
							f.close()
							password=lines[0].replace("\n","")
					
	
					#path="uid=lliurex," + self.llxvar("LDAP_ADMIN_PEOPLE_BASE_DN")
					try:
						path="cn=admin,"+self.llxvar("LDAP_BASE_DN")
					except:
						return None
						#path="uid=pepe,ou=Admins,ou=People,dc=ma5,dc=lliurex,dc=net"
					
					self.ldap.bind_s(path,password)
					print("OK")
					
					return True
					
					
				except Exception as l_ex:
					print(l_ex)
					try:
						url=self.llxvar("CLIENT_LDAP_URI")
					except Exception as e:
						print((e,""))
						return None
			self.core.pprint("GOLEM.LDAPMANAGER","Error connecting to ldap")			
			
		
		
		
	#def connect
	
	
	def print_list(self):
		
		
		a=self.ldap.search_s(self.llxvar("LDAP_BASE_DN"),ldap.SCOPE_SUBTREE,'sn='+'*')
		count=1
		for item in a:
			print(count)
			count+=1
			print(item)
				
		
	#def print_list
	
	@ldapmanager_connect
	def add_user(self,generic_mode,plantille,properties):
		
		uid=properties["uid"]
		user=LdapUser(properties)
		cn=""
		
		
		if (plantille=="Students"):
			
			try:
				groupinfo=grp.getgrnam('students')
				gidNumber=groupinfo[2]
				user.properties["gidNumber"]=str(gidNumber)			
			except Exception as e:
				self.log("add_user",e)
				#return "false"
				# \/ this should not be here \/
				user.properties["gidNumber"]="234"
				# /\ ==============  /\
						
			user.properties["profile"]="students"
			user.properties['sambaPrimaryGroupSID']=self.samba_id+"-"+user.properties["gidNumber"]
			cn="stuID"
			
			if "userPassword" not in properties:
				password="".join(random.sample(string.ascii_letters+string.digits, 4))
				user.properties["userPassword"]=password
			
		elif (plantille=="Teachers"):

			groupinfo=grp.getgrnam('teachers')
			gidNumber=groupinfo[2]
			user.properties["gidNumber"]=str(gidNumber)
			user.properties["profile"]="teachers"
			cn="teaID"
			
			if  "userPassword" not in properties:
				ssha_password,password=self.generate_random_ssha_password()
				user.properties["userPassword"]=password

		elif (plantille=="Other"):

			groupinfo=grp.getgrnam('others')
			gidNumber=groupinfo[2]
			user.properties["gidNumber"]=str(gidNumber)
			user.properties["profile"]="others"
			cn="otID"
		
			if "userPassword" not in properties:
				ssha_password,password=self.generate_random_ssha_password()
				user.properties["userPassword"]=password

	
		elif (plantille=="Admin"):
			
			#user.properties["sabayonProfileName"]="admin"
			p1=subprocess.Popen(["lliurex-userfuncs","llx_get_group_gid","admin"],stdout=subprocess.PIPE)
			output=p1.communicate()[0]
			gidNumber=output.replace("\n","")
			user.properties["gidNumber"]=str(gidNumber)
			user.properties["profile"]="admins"
			cn="otID"
		
			if "userPassword" not in properties:
				ssha_password,password=self.generate_random_ssha_password()
				user.properties["userPassword"]=password	
				
		if "userPassword" in properties:
			password=user.properties['userPassword']
			
		#else password variable should be available... it SHOULD 
		
		
		if "sambaNTPassword" not in user.properties:
			user.properties['sambaNTPassword']=passlib.hash.nthash.encrypt(password).upper()
		if "sambaLMPassword" not in user.properties:
			user.properties['sambaLMPassword']=passlib.hash.lmhash.encrypt(password).upper()
			
		user.properties['sambaPwdLastSet']=str(int(time.time()))
		
		path="uid="+user.uid+","+ "ou="+plantille+",ou=People," + self.llxvar("LDAP_BASE_DN")
		user.properties["path"]=path
		if "uidNumber" not in user.properties:
			ret,uidNumber=self.set_next_xid(plantille)
			if ret==False:
				#uidNumber is an exception in this case
				return uidNumber.message
			user.properties["uidNumber"]=str(uidNumber)
		else:
			uidNumber=user.properties["uidNumber"]
			
		user.properties['sambaSID']=self.samba_id+"-"+user.properties["uidNumber"]
		

		

		# ADD USER

		try:
			user_list=self.search_user(uid)
			if len(user_list)>0:
				raise ldap.ALREADY_EXISTS
				
			self.ldap.add_s(path,self.str_to_bytes(user.get_modlist()))
			group_list=self.add_to_generic_groups(plantille,user)
			if group_list!=None:
				user.properties["groups"]=group_list
			
			return user.properties
			
		except Exception as exc:
			
			
			if type(exc)==ldap.ALREADY_EXISTS:
				if not generic_mode:
					return "User already exists"
				else:
					
					count=0
					integer_found=False
					
					
					counter=len(uid)-1
					
					for pos in range(-len(uid)+1,1):
						try:
							integer=int(uid[pos*-1])
							counter-=1
						except:
							break	
							
					uid=uid[:counter+1]

					user_list=self.search_user(uid+"*")
					index_list=[]
					for item in user_list:
						list=item.uid.split(uid)
						if len(list)>1 and len(list[1])>0:
							try:
								lets_try=int(list[1])
								index_list.append(lets_try)
								
							except:
								pass
					
					index_list.sort()
					if len(index_list)>0:
						id=int(index_list[len(index_list)-1])
						id+=1
					else:
						id=1
						
					value=str(id)
					if id<10:
						value="0"+str(id)
						
					
					nonum_uid=uid
					uid=uid+value
					#print "Calculated uid: " + uid
					new_uid=uid
					new_attributes=[]
					
					user.properties["uid"]=new_uid
					user.properties["homeDirectory"]=base_home_dir+new_uid
					user.properties["gecos"]=new_uid
					user.properties['sambaHomePath']='\\'+new_uid
					user.properties['sambaProfilePath']='\\\\profiles\\'+new_uid
						
					if generic_mode:
						if user.properties["cn"].find(nonum_uid)!=-1:
							user.properties["cn"]=new_uid
								
						if user.properties["sn"].find(nonum_uid)!=-1:
							user.properties["sn"]=new_uid
						
						if user.properties["description"].find(nonum_uid)!=-1:
							user.properties["description"]=new_uid
						

					user.uid=new_uid
					user.properties["uid"]=new_uid
					path="uid="+user.uid+","+ "ou="+plantille+",ou=People," + self.llxvar("LDAP_BASE_DN")
					user.properties["path"]=path

					
					#print user.get_modlist()
					try:
						self.ldap.add_s(path,self.str_to_bytes(user.get_modlist()))
						group_list=self.add_to_generic_groups(plantille,user)
						if group_list!=None:
							user.properties["groups"]=group_list
						#print group_list
						return user.properties
						
					except Exception as inst:
						#print(inst)
						self.log("add_user",inst,"ldap.ALREADY_EXISTS branch")
						return inst[0]["desc"]
	

			else:
				#print(exc)
				self.log("add_user",exc)
				return exc[0]["desc"]

	#def add_user_def
	
	
	
	@ldapmanager_connect
	def set_next_id(self,cn,gidNumber=None):
		if gidNumber==None:
			mod=( ldap.MOD_REPLACE, 'gidNumber', str(self.get_next_id(cn)+1) )
		else:
			mod=( ldap.MOD_REPLACE, 'gidNumber', str(gidNumber) )
			
		mod_list=[]
		mod_list.append(mod)
		path="cn="+cn+",ou=Variables," + self.llxvar("LDAP_BASE_DN")
		mod_list=self.str_to_bytes(mod_list)
		self.ldap.modify_s(path,mod_list)		
		
	#def update_user_count_variable

	@ldapmanager_connect
	def get_next_id(self,cn):
		
		path="cn="+cn+",ou=Variables," + self.llxvar("LDAP_BASE_DN")
		
		a=self.ldap.search_s(path,ldap.SCOPE_SUBTREE)
		
		for x,y in a:
			if "gidNumber" in y: 
				return int(y['gidNumber'][0])
				
		
	#def get_next_id
		
	@ldapmanager_connect
	def modify_value(self,path,field,value):
		
		mod=( ldap.MOD_REPLACE, field, value )
		mod_list=[]
		mod_list.append(mod)
		try:
			mod_list=self.str_to_bytes(mod_list)
			self.ldap.modify_s(path,mod_list)
			return "true"
		except Exception as e:
			print(e)
			self.log("modify_value",e)
			return e[0]["desc"]
			
		
	#def modify_value
	
	
	@ldapmanager_connect
	def change_group_description(self,gid,description):
		
		mod=( ldap.MOD_REPLACE, "description", description )
		mod_list=[]
		mod_list.append(mod)                      
		path="cn="+gid+",ou=Managed,ou=Groups," + self.llxvar("LDAP_BASE_DN")
		try:
			mod_list=self.str_to_bytes(mod_list)
			self.ldap.modify_s(path,mod_list)
			return "true"
		except Exception as e:
			#print e
			self.log("change_group_description",e)
			return e[0]["desc"]				
		
		
	#def change_group_description
	
	@ldapmanager_connect
	def change_student_name(self,uid,name):
		#print "change student name!!!!!!"	
	
			
		mod=( ldap.MOD_REPLACE, "cn", name )
		mod_list=[]
		mod_list.append(mod)
		path="uid="+uid+","+ "ou=Students,ou=People," + self.llxvar("LDAP_BASE_DN")
		try:
			mod_list=self.str_to_bytes(mod_list)
			self.ldap.modify_s(path,mod_list)
			return "true"
		except Exception as e:
			self.log("change_student_name",e)
			return e[0]["desc"]		
		
		
	#def change_student_name
	

	
	@ldapmanager_connect
	def change_student_surname(self,uid,surname):
		
		#surname=unicode(surname).encode("utf-8")
		mod=( ldap.MOD_REPLACE, "sn", surname )
		mod_list=[]
		mod_list.append(mod)
		path="uid="+uid+","+ "ou=Students,ou=People," + self.llxvar("LDAP_BASE_DN")
		try:
			mod_list=self.str_to_bytes(mod_list)
			self.ldap.modify_s(path,mod_list)
			return "true"
		except Exception as e:
			self.log("change_student_surname",e)
			return e[0]["desc"]		
		
		
	#def change_student_name
	


	@ldapmanager_connect
	def change_password(self,path,password):
		
		try:
			password=password.encode("utf-8")
			if path.find("Students")!=-1:
				#str_to_bytes
				self.modify_value(path,"userPassword",password)
			else:
				#str_to_bytes
				self.modify_value(path,"userPassword",self.generate_ssha_password(password))
			self.modify_value(path,"sambaNTPassword",passlib.hash.nthash.encrypt(password).upper())
			self.modify_value(path,"sambaLMPassword",passlib.hash.lmhash.encrypt(password).upper())
			self.modify_value(path,"sambaPwdLastSet",str(int(time.time())))
			return "true"
		except Exception as e:
			print(e)
			self.log("change_password",e)
			return e[0]["desc"]
			
		
	#def modify_value	
	
	@ldapmanager_connect
	def change_user_password(self,uid,password):
		
		students="ou=Students,ou=People," + self.llxvar("LDAP_BASE_DN")
		path="uid="+uid+","+students
		return self.change_password(path,password)
		
	#def change_student_password
	
	@ldapmanager_connect
	def generic_student_to_itaca(self,uid,nia):
		
		students="ou=Students,ou=People," + self.llxvar("LDAP_BASE_DN")
		path="uid="+uid+","+students
		try:
			mod_list=[]
			mod=( ldap.MOD_REPLACE, "x-lliurex-usertype", "itaca" )
			mod_list.append(mod)
			mod=( ldap.MOD_ADD, "x-lliurex-nia", str(nia) )
			mod_list.append(mod)
			mod_list=self.str_to_bytes(mod_list)
			self.ldap.modify_s(path,mod_list)
			return "true"
			
		except Exception as e:
			self.log("generic_student_to_itaca",e)
			return e[0]["desc"]	

		
	#def generic_student_to_itaca
	
	
	@ldapmanager_connect
	def generic_teacher_to_itaca(self,uid,nif):
		
		teachers="ou=Teachers,ou=People," + self.llxvar("LDAP_BASE_DN")
		path="uid="+uid+","+teachers
		try:
			mod_list=[]
			mod=( ldap.MOD_REPLACE, "x-lliurex-usertype", "itaca" )
			mod_list.append(mod)
			mod=( ldap.MOD_ADD, "x-lliurex-nif",str(nif) )
			mod_list.append(mod)
			mod_list=self.str_to_bytes(mod_list)
			self.ldap.modify_s(path,mod_list)
			return "true"
			
		except Exception as e:
			self.log("generic_teacher_to_itaca",e)
			return e[0]["desc"]	

		
	#def generic_student_to_itaca	

	
	@ldapmanager_connect
	def add_generic_users(self,plantille,group_type,number,generic_name,pwd_generation_type,pwd=None):
		
		generated_users=[]
		
		for i in range(number):
			
			tmp_i=i+1
			
			val=str(tmp_i)
			
			if tmp_i < 10:
				val="0"+str(tmp_i)
			
			
			user_name=generic_name+ val
			
			generated_pwd=""
			
			if(pwd_generation_type==LdapManager.RANDOM_PASSWORDS):
				
				
				generated_pwd="".join(random.sample(string.ascii_letters+string.digits, 4))
				password=generated_pwd
				ok=True
				
				
				
			if(pwd_generation_type==LdapManager.SAME_PASSWORD):
				if(pwd!=None):
					password=pwd
					generated_pwd=password
				else:
					break
				
			if(pwd_generation_type==LdapManager.PASS_EQUALS_USER):
				password=user_name
				generated_pwd=password
			
			
			properties={}
			properties["uid"]=user_name
			properties["cn"]=user_name
			properties["sn"]=user_name
			properties["userPassword"]=password
			properties["x-lliurex-usertype"]="generic"
			
			generated_dic=self.add_user(True,plantille,properties)
			
			
			if type(generated_dic)==str:
				
				dic={}
				dic["ERROR"]=user_name + ":" + generated_dic
				generated_users.append(dic)
				
			else:
			
				
			
				if pwd_generation_type==LdapManager.PASS_EQUALS_USER:
					user_path=generated_dic["path"]
					generated_dic["userPassword"]=generated_dic["uid"]
					self.change_password(user_path,generated_dic["userPassword"])
					generated_pwd=generated_dic["userPassword"]
				else:
					generated_dic["userPassword"]=generated_pwd
				
				
				
				if generated_dic!=None:
					if group_type!=None:
						self.add_to_group_type(group_type,generated_dic["uid"])
						if "groups" not in generated_dic:
							generated_dic["groups"]=[]
						generated_dic["groups"].append(group_type)
									
					generated_users.append(generated_dic)
			
			
		return generated_users
			
			
			
		
		
	#def add_generic_users


	@ldapmanager_connect
	def add_to_generic_groups(self,plantille,user):
		
		teachers="cn=teachers,ou=Profiles,ou=Groups," + self.llxvar("LDAP_BASE_DN")
		students="cn=students,ou=Profiles,ou=Groups," + self.llxvar("LDAP_BASE_DN")
		others="cn=others,ou=Profiles,ou=Groups," + self.llxvar("LDAP_BASE_DN")
		user_path="uid="+user.uid+",ou="+plantille+",ou=People," + self.llxvar("LDAP_BASE_DN")
		teachers_groups=["dialout","cdrom","floppy","audio","dip","video","plugdev","netdev","vboxusers","fuse","epoptes","bluetooth"]
		students_groups=["dialout","cdrom","floppy","audio","dip","video","plugdev","netdev","vboxusers","fuse","bluetooth"]
		
		if(plantille=="Teachers"):
			
			mod_list=[]
			mod2=(ldap.MOD_ADD,'memberUid',user.uid)
			mod_list.append(mod2)
			try:
				mod_list=self.str_to_bytes(mod_list)
				self.ldap.modify_s(teachers,mod_list)
				for group in teachers_groups:
					mod=(ldap.MOD_ADD,"memberUid",user.uid)
					mod_list=[]
					mod_list.append(mod)
					group_path="cn=" + group +",ou=System,ou=Groups," + self.llxvar("LDAP_BASE_DN")
					mod_list=self.str_to_bytes(mod_list)
					self.ldap.modify_s(group_path,mod_list)
					
				teachers_groups.append("teachers")
				return teachers_groups
				
			except Exception as e:
				self.log("add_to_generic_groups",e,"Teachers")
				print(e)
				return None
			
			
		
		if(plantille=="Students"):

			#mod=(ldap.MOD_ADD,'member',user_path)
			mod_list=[]
			#mod_list.append(mod)
			mod2=(ldap.MOD_ADD,'memberUid',user.uid)
			mod_list.append(mod2)

			try:
				mod_list=self.str_to_bytes(mod_list)
				self.ldap.modify_s(students,mod_list)
				
				for group in students_groups:
					mod=(ldap.MOD_ADD,"memberUid",user.uid)
					mod_list=[]
					mod_list.append(mod)
					group_path="cn=" + group +",ou=System,ou=Groups," + self.llxvar("LDAP_BASE_DN")
					mod_list=self.str_to_bytes(mod_list)
					self.ldap.modify_s(group_path,mod_list)
				
				students_groups.append("students")
				return students_groups
				
				
			except Exception as e:
				self.log("add_to_generic_groups",e,"Students")
				print(e)
				return None
			
		if(plantille=="Other"):

			mod=(ldap.MOD_ADD,'member',user_path)
			mod_list=[]
			mod_list.append(mod)
			
			try:
				mod_list=self.str_to_bytes(mod_list)
				self.ldap.modify_s(others,mod_list)
				for group in students_groups:
					mod=(ldap.MOD_ADD,"memberUid",user.uid)
					mod_list=[]
					mod_list.append(mod)
					group_path="cn=" + group +",ou=System,ou=Groups," + self.llxvar("LDAP_BASE_DN")
					mod_list=self.str_to_bytes(mod_list)
					self.ldap.modify_s(group_path,mod_list)
					
				students_groups.append("others")
				return students_groups
					
			except Exception as e:
				self.log("add_to_generic_groups",e,"Others")
				print(e)
				return None
		
		
	#def add_to_generic_groups
	
	
	@ldapmanager_connect
	def add_to_group_type(self,cn,uid):
		
		path="cn=" + cn + ",ou=Managed,ou=Groups," + self.llxvar("LDAP_BASE_DN")
		
		
		mod=(ldap.MOD_ADD,'memberUid',uid)
		mod_list=[]
		mod_list.append(mod)
			
		print("*** ADDING " + uid + " to " + path)
		try:
			mod_list=self.str_to_bytes(mod_list)
			self.ldap.modify_s(path,mod_list)
			return "true"
		except Exception as e:
			self.log("add_to_group_type",e,"Teachers")
			return e[0]["desc"]
		
		
		
	#def add_to_group_type
	
	
	@ldapmanager_connect
	def add_teacher_to_admins(self,uid):
		
		path="cn=admins,ou=Profiles,ou=Groups," + self.llxvar("LDAP_BASE_DN")
		
		user_dn="uid="+uid+",ou=Teachers,ou=People," + self.llxvar("LDAP_BASE_DN")
		
		mod_list=[]
		mod=(ldap.MOD_ADD,"memberUid",uid)
		mod_list.append(mod)
		
		#print "*** ADDING " + uid + " to admins"
		try:
			mod_list=self.str_to_bytes(mod_list)
			ret=self.ldap.modify_s(path,mod_list)
			return "true"
		except Exception as e:
			print(e)
			if type(e)==ldap.TYPE_OR_VALUE_EXISTS:
				return "true"
			else:
				self.log("add_teacher_to_admins",e,uid)
				return e[0]["desc"]
		
		
	#def add_teacher_to_admins
	
	
	@ldapmanager_connect
	def del_teacher_from_admins(self,uid):

		path="cn=admins,ou=Profiles,ou=Groups," + self.llxvar("LDAP_BASE_DN")
		
		user_dn="uid="+uid+",ou=Teachers,ou=People," + self.llxvar("LDAP_BASE_DN")
		
		
		mod_list=[]
		mod=(ldap.MOD_DELETE,"memberUid",uid)
		mod_list.append(mod)
		
		#print "*** DELETING " + uid + " from admins"
		try:
			mod_list=self.str_to_bytes(mod_list)
			self.ldap.modify_s(path,mod_list)
			return "true"
		except Exception as e:
			
			if type(e)==ldap.NO_SUCH_ATTRIBUTE:
				return "true"
			else:
				self.log("del_teacher_from_admins",e,uid)
				return e[0]["desc"]


		
	#def del_teacher_from_admins
	
	@ldapmanager_connect
	def custom_search(self,basedn,filter="objectClass=*",attrl=None):
		
		try:
			
			result=self.ldap.search_s(basedn,ldap.SCOPE_SUBTREE,filter,attrl)
			
			return {"status":True,"msg":result}
			
			
		except Exception as e:
			
			return {"status":False,"msg":"Captured exception: %s"%e}
		
	#def custom_search
	
	
	@ldapmanager_connect
	def full_search(self,uid):
		
		ret={}
		
		result=self.ldap.search_s("ou=People,"+self.llxvar("LDAP_BASE_DN"),ldap.SCOPE_SUBTREE,"uid="+uid)
		#ret_list.append(result)
		user_list=[]
		for item in result:
			path,info=item
			d={}
			d[path]={}
			try:
				for key in ["uid","uidNumber","gidNumber","sambaSID","objectClass","loginShell","homeDirectory","sambaAcctFlags"]:
					try:
						if key!="objectClass":
							d[path][key]=info[key][0]
						else:
							d[path][key]=info[key]
					except Exception as e:
						if "exception" not in d[path]:
							d[path]["exception"]=[]
						d[path]["exception"].append(str(e))
					
				user_list.append(d)
			except:
				continue
				
		ret["users"]=user_list
		
		path="cn=admins,ou=Profiles,ou=Groups," + self.llxvar("LDAP_BASE_DN")
		result=self.ldap.search_s(path,ldap.SCOPE_SUBTREE)
		
		admin_list=[]
		#print result
		for item in result:
			path,info=item
			d={}
			d[path]={}			
			for key in ["sambaGroupType","cn","sambaSID","gidNumber","description","objectClass","memberUid"]:
				try:
					if key!="objectClass" and key!="memberUid":
						d[path][key]=info[key][0]
					else:
						d[path][key]=info[key]
					
				except Exception as e:
					print((path,e))
					if "exception" not in d[path]:
						d[path]["exception"]=[]
					d[path]["exception"].append(str(e))
				
			admin_list.append(d)
			
		ret["admins"]=admin_list
		
		path="ou=Managed,ou=Groups,"+self.llxvar("LDAP_BASE_DN")
		result=self.ldap.search_s(path,ldap.SCOPE_SUBTREE)
		group_list=[]
		
		for item in result:
			path,info=item
			
			d={}
			d[path]={}
			d[path]["objectClass"]=info["objectClass"]
			if "ou" in info:
				
				try:
					d[path]["ou"]=info["ou"][0]
					d[path]["x-lliurex-xid-counter"]=info["x-lliurex-xid-counter"][0]
				except Exception as e:
					d[path]["exception"]=[]
					d[path]["exception"].append(str(e))
			else:
				for key in ["sambaGroupType","cn","x-lliurex-grouptype","sambaSID","gidNumber","description","memberUid","objectClass"]:
					try:
						if key!="memberUid" and key!="ObjectClass":
							d[path][key]=info[key][0]
						else:
							d[path][key]=info[key]
						
						
					except Exception as e:
						if "exception" not in d[path]:
							d[path]["exception"]=[]
						d[path]["exception"].append(str(e))
					
			group_list.append(d)
		
		
		ret["groups"]=group_list
		
		#ret_list.append(group_result)
		
		return ret
		
		
		
		
		
	#def search_user_native
	
	@ldapmanager_connect
	def search_user(self,uid):
		#ou=Students,ou=People
		result=self.ldap.search_s("ou=People,"+self.llxvar("LDAP_BASE_DN"),ldap.SCOPE_SUBTREE,"uid="+uid)
		user_list=[]
		
		path="cn=admins,ou=Profiles,ou=Groups," + self.llxvar("LDAP_BASE_DN")
		ret=self.ldap.search_s(path,ldap.SCOPE_SUBTREE)
		admins_list=ret[0][1]["memberUid"]
		
		path="ou=Managed,ou=Groups,"+self.llxvar("LDAP_BASE_DN")
		group_result=self.ldap.search_s(path,ldap.SCOPE_SUBTREE)
		

		for item in result:
			path,properties_dic=item
			
			group_list=[]
			
			for group in group_result:
				g_path,dic=group
				if "memberUid" in dic:
					if properties_dic["uid"][0] in dic["memberUid"]:
						tmp=g_path.split(",")
						cn=tmp[0].split("=")[1]
						group_list.append(cn)			
		
			
			prop={}
			try:
				prop["uid"]=properties_dic["uid"][0]
				prop["cn"]=properties_dic["cn"][0]
				prop["sn"]=properties_dic["sn"][0]
			except Exception as ex:
				continue
			user=LdapUser(prop)
			
			if path.find("Student")!=-1:
				user.properties["profile"]="students"
			if path.find("Teacher")!=-1:
				user.properties["profile"]="teachers"
			if path.find("Other")!=-1:
				user.properties["profile"]="others"
			if path.find("Admin")!=-1:
				user.properties["profile"]="admin"
			
			user.properties["uidNumber"]=properties_dic["uidNumber"][0].decode("utf-8")
			user.properties["gidNumber"]=properties_dic["gidNumber"][0].decode("utf-8")
			user.properties["path"]=path
			user.properties["groups"]=group_list
			
			if "x-lliurex-usertype" in properties_dic:
				user.properties["x-lliurex-usertype"]=properties_dic["x-lliurex-usertype"][0].decode("utf-8")
				
			if "x-lliurex-nia" in properties_dic:
				user.properties["x-lliurex-nia"]=properties_dic["x-lliurex-nia"][0].decode("utf-8")
				
			if "x-lliurex-nif" in properties_dic:
				user.properties["x-lliurex-nif"]=properties_dic["x-lliurex-nif"][0].decode("utf-8")
			
			if user.properties["uid"].encode("utf-8") in admins_list:
				user.properties["is_admin"]=True
			else:
				user.properties["is_admin"]=False
			
			user_list.append(user)
			 
		return user_list		
		
	#def search_user
	
	
	@ldapmanager_connect
	def light_search(self):
		result=self.ldap.search_s("ou=People,"+self.llxvar("LDAP_BASE_DN"),ldap.SCOPE_SUBTREE,"uid=*")
		
		user_list=[]
		
		
		
		for item in result:
			

			path,properties_dic=item
			desc=""
			if "description" in properties_dic:
				desc=properties_dic["description"][0]
				
			
			
			profile=""
			
			if path.find("Student")!=-1:
				profile="students"
			if path.find("Teacher")!=-1:
				profile="teachers"
			if path.find("Other")!=-1:
				profile="others"
			if path.find("Admin")!=-1:
				profile="admin"			
			
			#user_list.append((properties_dic["uid"][0],path,properties_dic["cn"][0],properties_dic["sn"][0],desc))
			user_list.append((path,properties_dic["uid"][0].decode("utf-8"),properties_dic["uidNumber"][0].decode("utf-8"),properties_dic["cn"][0].decode("utf-8"),properties_dic["sn"][0].decode("utf-8"),profile))
			
			
		return user_list			
		
	#def light_search
	
	
	@ldapmanager_connect
	def search_user_with_filter(self,filter):
		listldapusers=self.ldap.search_s("ou=People,"+self.llxvar("LDAP_BASE_DN"),ldap.SCOPE_SUBTREE,filter)
		result = {}
		for x in listldapusers:
			#print x[0]
			upgradeuser = {}
			if x[0].find("Student")!=-1:
				upgradeuser["profile"]="students"
			elif x[0].find("Teachers")!=-1:
				upgradeuser["profile"]="teachers"
			elif x[0].find("Admin")!=-1:
				upgradeuser["profile"]="admins"
			
			for key,value in x[1].items():
				if len(value) == 1:
					upgradeuser[key] = value[0]
				else:
					upgradeuser[key] = value
			#upgradeuser['profile'] = x[1]['profile'][0]
			
				
			result[upgradeuser['uid']] = upgradeuser
		return result
	
	
	@ldapmanager_connect
	def search_user_dic(self,uid):
		#ou=Students,ou=People
		result=self.ldap.search_s("ou=People,"+self.llxvar("LDAP_BASE_DN"),ldap.SCOPE_SUBTREE,"uid="+uid)
		
		user_list=[]
		
		for item in result:
			path,properties_dic=item
			prop={}
			prop["uid"]=properties_dic["uid"][0]
			prop["cn"]=properties_dic["cn"][0]
			prop["sn"]=properties_dic["sn"][0]
			user=LdapUser(prop)
			user.properties["path"]=path
			user_list.append(user.properties)
			 
			
		return user_list		
	
	
	@ldapmanager_connect
	def search_students(self,uid):
		#ou=Students,ou=People
		result=self.ldap.search_s("ou=Students,ou=People,"+self.llxvar("LDAP_BASE_DN"),ldap.SCOPE_SUBTREE,"uid="+uid)
		
		user_list=[]
		
		for item in result:
			path,properties_dic=item
			prop={}
			prop["uid"]=properties_dic["uid"][0]
			prop["cn"]=properties_dic["cn"][0]
			prop["sn"]=properties_dic["sn"][0]			
			user=LdapUser(prop)
			user.properties["path"]=path
			user_list.append(user)
			

		return user_list		
		
	#def search_user

	
	@ldapmanager_connect
	def search_teachers(self,uid):
		#ou=Students,ou=People
		result=self.ldap.search_s("ou=Teachers,ou=People,"+self.llxvar("LDAP_BASE_DN"),ldap.SCOPE_SUBTREE,"uid="+uid)
		
		user_list=[]
		
		for item in result:
			path,properties_dic=item
			prop={}
			prop["uid"]=properties_dic["uid"][0]
			prop["cn"]=properties_dic["cn"][0]
			prop["sn"]=properties_dic["sn"][0]
			user=LdapUser(prop)
			user.properties["path"]=path
			user_list.append(user)
			
		return user_list		
		
	#def search_user		
	
	
	@ldapmanager_connect
	def delete_user(self,uid):
		
		user=self.search_user(uid)
		if user[0].properties["path"].find("Students")!=-1:
			
			try:
				user[0].properties["groups"]=self.get_generic_groups(uid)
				user[0].properties["groups"].append("students")
				self.delete_student(uid)
				return user[0].properties
			except:
				self.log("delete_user",e,"Student: " + uid)
				return None
		
		if user[0].properties["path"].find("Teachers")!=-1:
			
			try:
				user[0].properties["groups"]=self.get_generic_groups(uid)
				user[0].properties["groups"].append("teachers")
				self.delete_teacher(uid)
				return user[0].properties
			except:
				self.log("delete_user",e,"Teacher: " + uid)
				return None
		
		
	#def delete_user
	
	@ldapmanager_connect
	def delete_student(self,uid):
	
		try:

			group_list=self.get_groups(uid)
			for group in group_list:
				self.del_user_from_group(uid,group)
				
			path="uid="+uid+",ou=Students,ou=People,"+self.llxvar("LDAP_BASE_DN")	
			group_list=self.get_generic_groups(uid)
			
			for group in group_list:
				self.del_user_from_generic_group(uid,group)		

			self.del_student_from_student_group(uid)
			self.ldap.delete_s(path)
			return "true"

			
		except Exception as e:
			self.log("delete_student",e,uid)
			return e[0]['desc']
			
	
	#def delete_user
	
	@ldapmanager_connect
	def delete_other(self,uid):
	
		try:
			group_list=self.get_groups(uid)

			for group in group_list:
				self.del_user_from_group(uid,group)
				
			path="uid="+uid+",ou=Other,ou=People,"+self.llxvar("LDAP_BASE_DN")	
			group_list=self.get_generic_groups(uid)
			
			for group in group_list:
				self.del_user_from_generic_group(uid,group)		

			self.del_student_from_student_group(uid)
			self.ldap.delete_s(path)
			return "true"

		except Exception as e:
			self.log("delete_other",e,uid)
			return e[0]['desc']
			
	
	#def delete_user

	
	
	
	@ldapmanager_connect
	def delete_teacher(self,uid):
	
		try:

			group_list=self.get_groups(uid)
			for group in group_list:
				self.del_user_from_group(uid,group)
				
			path="uid="+uid+",ou=Teachers,ou=People,"+self.llxvar("LDAP_BASE_DN")	
			group_list=self.get_generic_groups(uid)

			for group in group_list:
				self.del_user_from_generic_group(uid,group)		

			self.del_teacher_from_teacher_group(uid)
			self.ldap.delete_s(path)
			return "true"
			
		except Exception as e:
			self.log("delete_teacher",e,uid)
			return e[0]['desc']
			
	
	#def delete_user

	
	@ldapmanager_connect
	def get_groups(self,uid):
		
		path="ou=Managed,ou=Groups,"+self.llxvar("LDAP_BASE_DN")
		result=self.ldap.search_s(path,ldap.SCOPE_SUBTREE)
		group_list=[]
		for group in result:
			g_path,dic=group
			if "memberUid" in dic:
				if uid in dic["memberUid"]:
					tmp=g_path.split(",")
					cn=tmp[0].split("=")[1]
					group_list.append(cn)
					
		return group_list			
		
	#def get_groups
	
	
	@ldapmanager_connect
	def get_available_groups(self):
		
		path="ou=Managed,ou=Groups,"+self.llxvar("LDAP_BASE_DN")
		result=self.ldap.search_s(path,ldap.SCOPE_SUBTREE)

		group_list=[]
		for group in result:
			g_path,dic=group
			dic["path"]=g_path
			if b"posixGroup" in dic["objectClass"]:
				dic["cn"][0]=dic["cn"][0].decode("utf-8")
				dic["description"][0]=dic["description"][0].decode("utf-8")
				dic["gidNumber"][0]=dic["gidNumber"][0].decode("utf-8")
				dic["x-lliurex-grouptype"][0]=dic["x-lliurex-grouptype"][0].decode("utf-8")
				
				if "memberUid" in dic:
					count=0
					for member in dic["memberUid"]:
						dic["memberUid"][count]=member.decode("utf-8")
						count+=1
				
				group_list.append(dic)
		
		
		return group_list	
		
	#def get_available_groups
	
	
	@ldapmanager_connect
	def get_generic_groups(self,uid):
		
		
		path="ou=System,ou=Groups,"+self.llxvar("LDAP_BASE_DN")
		result=self.ldap.search_s(path,ldap.SCOPE_SUBTREE)
		group_list=[]
		for group in result:
			g_path,dic=group
			if "memberUid" in dic:
				
				if uid in dic["memberUid"]:
					tmp=g_path.split(",")
					cn=tmp[0].split("=")[1]
					group_list.append(cn)
					
		return group_list			
		
	#def get_generic_groups
	
	
	@ldapmanager_connect
	def del_student_from_student_group(self,uid):
		
		path="cn=students,ou=Profiles,ou=Groups," + self.llxvar("LDAP_BASE_DN")
		user_dn="uid=" + uid + ",ou=Students,ou=People," + self.llxvar("LDAP_BASE_DN")
		#print user_dn
		mod_list=[]
		mod=(ldap.MOD_DELETE,"memberUid",uid)
		mod_list.append(mod)
		try:
			mod_list=self.str_to_bytes(mod_list)
			self.ldap.modify_s(path,mod_list)
		except Exception as e:
			self.log("del_student_from_student_group",e,uid)
			return e[0]['desc']
		
	#def del_student_from_student_group
	
	
	@ldapmanager_connect
	def del_teacher_from_teacher_group(self,uid):
		
		path="cn=teachers,ou=Profiles,ou=Groups," + self.llxvar("LDAP_BASE_DN")
		user_dn="uid=" + uid + ",ou=Teachers,ou=People," + self.llxvar("LDAP_BASE_DN")
		#print user_dn
		mod_list=[]
		mod=(ldap.MOD_DELETE,"memberUid",uid)
		mod_list.append(mod)
		try:
			mod_list=self.str_to_bytes(mod_list)
			self.ldap.modify_s(path,mod_list)
		except Exception as e:
			self.log("del_teacher_from_teacher_group",e,uid)
			return e[0]["desc"]
		
	#def del_student_from_student_group	
	
	
	@ldapmanager_connect
	def del_user_from_group(self,uid,group_cn):
		
		mod=(ldap.MOD_DELETE,"memberUid",uid)
		mod_list=[]
		mod_list.append(mod)
		path="cn="+group_cn+",ou=Managed,ou=Groups,"+self.llxvar("LDAP_BASE_DN")
		try:
			mod_list=self.str_to_bytes(mod_list)
			self.ldap.modify_s(path,mod_list)
			return "true"
		except Exception as e:
			#print e
			self.log("del_user_from_group",e,uid)
			return e[0]["desc"]
		
	#def del_user_from_group

	@ldapmanager_connect
	def del_user_from_generic_group(self,uid,group_cn):
		
		mod=(ldap.MOD_DELETE,"memberUid",uid)
		mod_list=[]
		mod_list.append(mod)
		path="cn="+group_cn+",ou=System,ou=Groups,"+self.llxvar("LDAP_BASE_DN")
		try:
			mod_list=self.str_to_bytes(mod_list)
			self.ldap.modify_s(path,mod_list)
		except Exception as e:
			self.log("del_user_from_generic_group",e,uid + " " + group_cn)
			return e[0]["desc"]
			
		
	#def del_user_from_group

	@ldapmanager_connect
	def add_group(self,properties):
		
		path="cn="+str(properties["cn"])+",ou=Managed,ou=Groups," + self.llxvar("LDAP_BASE_DN")
		
		group=LdapGroup(properties)
		
		try:
			gidNumber=self.set_next_xgid()[1]
			group.attributes.append(("gidNumber",str(gidNumber)))
			group.attributes.append(("sambaSID",self.samba_id+"-"+str(gidNumber)))
			group.attributes.append(("sambaGroupType",str(2)))
			self.ldap.add_s(path,self.str_to_bytes(group.attributes))
			return "true"
		except Exception as e:
			self.log("add_group",e)
			print(e)
			return str(e)
		
	#def add_group
	
	@ldapmanager_connect
	def print_group_list(self,cn):
		
		
		a=self.ldap.search_s(self.llxvar("LDAP_BASE_DN"),ldap.SCOPE_SUBTREE,"cn="+cn)
		count=1
		for item in a:
			count+=1
			print(item)
				
		
	#def print_list	
	
	
	@ldapmanager_connect
	def search_group(self,cn):
		
		result=self.ldap.search_s("ou=Managed,ou=Groups,"+self.llxvar("LDAP_BASE_DN"),ldap.SCOPE_SUBTREE,"cn="+cn)
		
		group_list=[]
		
		for item in result:
			path,properties_dic=item
						
			prop={}
			prop["cn"]=cn
							
			group=LdapGroup(prop)
			group.properties["path"]=path
			if "memberUid" in properties_dic:
				group.properties["memberUid"]=properties_dic["memberUid"]
				
			group_list.append(group)

		return group_list
		
	#def search_group
	
	
	@ldapmanager_connect
	def get_dn(self,uid):
		
		result=self.ldap.search_s("ou=People,"+self.llxvar("LDAP_BASE_DN"),ldap.SCOPE_SUBTREE,"uid="+uid)
		
		user_list=[]
		
		path="ou=Managed,ou=Groups,"+self.llxvar("LDAP_BASE_DN")
		group_result=self.ldap.search_s(path,ldap.SCOPE_SUBTREE)
		
		
		for item in result:
			path,properties_dic=item
			return path
		
	#def get_dn

	
	@ldapmanager_connect
	def get_students_passwords(self):
		
		result=self.ldap.search_s("ou=Students,ou=People,"+self.llxvar("LDAP_BASE_DN"),ldap.SCOPE_SUBTREE,"uid=*")
		ret_list = []
		
		for item in result:
			
			try:
				path,dic=item
				user={}
				if "userPassword" in dic:
					user['passwd']=dic["userPassword"][0].decode("utf-8")
				if "sambaNTPassword" in dic:
					user['sambaNTPassword']=dic["sambaNTPassword"][0].decode("utf-8")
				if "sambaLMPassword" in dic:
					user['sambaLMPassword']=dic["sambaLMPassword"][0].decode("utf-8")
				if "sn" in dic:
					user['sn']=dic["sn"][0].decode("utf-8")
				if "cn" in dic:
					user['cn']=dic["cn"][0].decode("utf-8")
				if "uid" in dic:
					user['uid']=dic["uid"][0].decode("utf-8")
				ret_list.append(user)
			except Exception as e:
				pass
				
		
		
		return ret_list
		
	#def get_students_passwords



	@ldapmanager_connect
	def get_teachers_passwords(self):
		
		result=self.ldap.search_s("ou=Teachers,ou=People,"+self.llxvar("LDAP_BASE_DN"),ldap.SCOPE_SUBTREE,"uid=*")
		ret_list = []
		
		for item in result:
			
			try:
				path,dic=item
				user={}
				if "userPassword" in dic:
					user['passwd']=dic["userPassword"][0].decode("utf-8")
				if "sambaNTPassword" in dic:
					user['sambaNTPassword']=dic["sambaNTPassword"][0].decode("utf-8")
				if "sambaLMPassword" in dic:
					user['sambaLMPassword']=dic["sambaLMPassword"][0].decode("utf-8")
				if "sn" in dic:
					user['sn']=dic["sn"][0].decode("utf-8")
				if "cn" in dic:
					user['cn']=dic["cn"][0].decode("utf-8")
				if "uid" in dic:
					user['uid']=dic["uid"][0].decode("utf-8")
				ret_list.append(user)
			except Exception as e:
				pass
				
		
		
		return ret_list
		
	#def get_students_passwords

	@ldapmanager_connect
	def delete_group(self,cn):
		
		path="cn=" + cn + ",ou=Managed,ou=Groups," + self.llxvar("LDAP_BASE_DN")
		print("Deleting group " + path)
		try:
			self.ldap.delete_s(path)
			return "true"
		except Exception as e:
			self.log("delete_group",e,cn)
			return e[0]["desc"]
		
	#def delete_group
	
	'''
		uid_list : list
		no_group_user : Boolean
	'''
	@ldapmanager_connect
	def freeze_user(self,uid_list,no_group_user=True):
		
		frozen_users={}
		
		for uid in uid_list:
			if uid!=None and len(uid)>0:
				path="uid=" + uid + ",ou=Students,ou=People," + self.llxvar("LDAP_BASE_DN")
				mod_list=[]
				mod=( ldap.MOD_REPLACE, "x-lliurex-freeze", "True" )
				mod_list.append(mod)
				try:
					mod_list=self.str_to_bytes(mod_list)
					self.ldap.modify_s(path,mod_list)
					frozen_users[uid]=True
				except Exception as e:
					self.log("modify_value",e)
					frozen_users[uid]=str(e)
				
		return frozen_users
			
	#def freeze_user
	
	@ldapmanager_connect
	def unfreeze_user(self,uid_list):

		unfrozen_users={}
		
		for uid in uid_list:
			if uid != None and len(uid) > 0 :
				try:
					path="uid=" + uid + ",ou=Students,ou=People," + self.llxvar("LDAP_BASE_DN")
					mod_list=[]
					mod=(ldap.MOD_REPLACE,'x-lliurex-freeze',"False")
					mod_list.append(mod)
					mod_list=self.str_to_bytes(mod_list)
					self.ldap.modify_s(path,mod_list)
					unfrozen_users[uid]=True
				except Exception as exc:
					self.log("unfreeze_user",e,"1")
					print(exc[0]['desc'])
					unfrozen_users[uid]=str(e)

		return unfrozen_users
					

	#def unfreeze_user
	
	@ldapmanager_connect
	def freeze_group(self,group_list):
		
		frozen_groups={}
		
		for cn in group_list:
			try:
				path="cn=" + cn + ",ou=Managed,ou=Groups," + self.llxvar("LDAP_BASE_DN")
				mod_list=[]
				mod=(ldap.MOD_REPLACE,'x-lliurex-freeze',"True")
				mod_list.append(mod)
				mod_list=self.str_to_bytes(mod_list)
				self.ldap.modify_s(path,mod_list)
				frozen_groups[cn]=True
			except Exception as e:
				print(e)
				frozen_groups[cn]=str(e)
				
		return frozen_groups
				
	#def freeze_group
	
	@ldapmanager_connect
	def unfreeze_group(self,group_list):

		unfrozen_groups={}
		
		for cn in group_list:
			try:
				path="cn=" + cn + ",ou=Managed,ou=Groups," + self.llxvar("LDAP_BASE_DN")
				mod_list=[]
				mod=(ldap.MOD_REPLACE,'x-lliurex-freeze',"False")
				mod_list.append(mod)
				mod_list=self.str_to_bytes(mod_list)
				self.ldap.modify_s(path,mod_list)
				unfrozen_groups[cn]=True
			except Exception as e:
				print(e)
				unfrozen_groups[cn]=str(e)
				
		return unfrozen_groups
		
	#def unfreeze_group
	
	@ldapmanager_connect
	def is_frozen_user(self,uid):

		try:
			
			users = self.ldap.search_s("ou=People,"+self.llxvar("LDAP_BASE_DN"),ldap.SCOPE_SUBTREE,"(uid=%s)"%uid)
			for x,y in users:
				
				
				if "x-lliurex-freeze" in y:
					if y["x-lliurex-freeze"][0]=="True":
						return True
				
			group_list=self.get_groups(uid)
			
			frozen_groups=self.get_frozen_groups()
			
			for group in group_list:
				if group in frozen_groups:
					return True
					
			return False
			
		except:
			
			return False
					
	# def is_freeze_user
	
	
	@ldapmanager_connect
	def get_frozen_users(self):
		
		path="ou=Students,ou=People," + self.llxvar("LDAP_BASE_DN")
		users=self.ldap.search_s(path,ldap.SCOPE_SUBTREE)
		lst=[]
		for x,y in users:
			if "x-lliurex-freeze" in y:
				if y["x-lliurex-freeze"][0]==b"True":
					lst.append(y["uid"][0].decode("utf-8"))
		
		return lst
		
		
	#def get_frozen_users
	
	
	@ldapmanager_connect
	def get_frozen_groups(self):
		
		path="ou=Managed,ou=Groups," + self.llxvar("LDAP_BASE_DN")
		groups=self.ldap.search_s(path,ldap.SCOPE_SUBTREE)
		lst=[]
		for x,y in groups:
			if "x-lliurex-freeze" in y:
				if y["x-lliurex-freeze"][0]==b"True":
					lst.append(y["cn"][0].decode("utf-8"))
		
		return lst
		
	#def get_frozen_groups
	
	
#class LdapManager

if __name__=="__main__":
	
	
	
	ldapman=LdapManager([])
	
	#ldapman.get_samba_id2()
	
	#ldapman.print_list()
	
	#add_generic_users(self,plantille,group_type,number,generic_name,pwd_generation_type,pwd=None)
	#RANDOM_PASSWORDS
	#SAME_PASSWORD
	#PASS_EQUALS_USER
	#print ldapman.add_generic_users("Students",None,1,"kha",ldapman.PASS_EQUALS_USER)


	properties={}
	properties['uid']='pepa2'
	properties['cn']='pepa'
	properties['userPassword']="lliurex"
	#properties['displayName']='pepito'
	properties['sn']='palotes'
	

	#print ldapman.add_user(True,"Students",properties)

	#print ldapman.add_teacher_to_admins("micomi")

	#ldapman.del_teacher_from_admins("profe01")


	#print ldapman.generate_uid("ana de iratxe","garcia de las torres")
	'''
	list=ldapman.search_user("*")
	
	for item in list:
		print item.properties["uid"]

	print ""
	'''
	
	
	
	
	
	
	
	
	
	
	
	
	
	
