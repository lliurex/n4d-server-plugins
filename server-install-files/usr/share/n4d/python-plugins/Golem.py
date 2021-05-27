# -*- coding: utf-8 -*-
import imp
import ldap
import sys
import subprocess
import grp
import shutil
import threading
import magic
import pyinotify
import time
import shutil
import os

import n4d.server.core
import n4d.responses

from pyinotify import WatchManager, Notifier, ThreadedNotifier, EventsCodes, ProcessEvent


class Golem:


	SUPPORT_PATH="/usr/share/n4d/python-plugins/support/"
	LDAP_LOG="/var/lib/ldap/"
	
	def __init__(self):
		
		self.core=n4d.server.core.Core.get_core()
		
	#def init
	
	def startup(self,options):
		
		
		try:
			self.mime=magic.open(magic.MAGIC_MIME)
			self.mime.load()
			self.obj=imp.load_source("LdapManager",Golem.SUPPORT_PATH + "LdapManager.py")
			obj3=imp.load_source("NetFilesManager",Golem.SUPPORT_PATH + "NetFilesManager.py")
			obj4=imp.load_source("PasswordManager",Golem.SUPPORT_PATH + "PasswordManager.py")
			obj5=imp.load_source("GesItaManager",Golem.SUPPORT_PATH + "GesItaManager.py")
			#obj6=imp.load_source("FileOperations",Golem.SUPPORT_PATH + "FileOperations.py")
			obj7=imp.load_source("PeterPan",Golem.SUPPORT_PATH + "PeterPan.py")
			self.ldap=self.obj.LdapManager()
			self.netfiles=obj3.NetFilesManager()
			self.pw=obj4.PasswordManager()
			self.itaca=obj5.GesItaManager()
			#self.file_operations=obj6.FileOperations()
			self.peter_pan=obj7.PeterPan()
			self.try_count=0
			self.sharefunctions = {}
			
			# Let's disable this for now. 29/06/18
			'''
			if objects["VariablesManager"].get_variable("MASTER_SERVER_IP")!=None:
				p=subprocess.Popen(["gluster volume info"],shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()[1]
				if 'No volumes present' in p:
					#Light version. Does not chown existing net files
					self.regenerate_net_files(1)
					self.start_inotify()
					
			'''
			
		except Exception as e:
			print(e)
		
	#def __init__
	

	def llxvars(self,var_name):
		
		return self.core.get_variable(var_name)["return"]
		
	#def llxvars


	def start_inotify(self):

		t=threading.Thread(target=self._inotify)
		t.daemon=True
		t.start()

	#def start_inotify
		
	def _inotify(self):
		
		wm=WatchManager()
		mask=pyinotify.ALL_EVENTS
			
		class Process_handler(ProcessEvent):
				
			def __init__(self,main):
				
				self.main=main
				self.count=0
				self.in_modify=False
				
			def process_IN_MODIFY(self,event):
				if not self.in_modify:
					self.in_modify=True
					time.sleep(2)
					# light version. Does not chown existing net files
					self.main.regenerate_net_files(1)
					time.sleep(2)
					self.in_modify=False


	
		notifier=Notifier(wm,Process_handler(self))
		wdd=wm.add_watch(Golem.LDAP_LOG,mask,rec=True)
			
		while True:
			try:
					
				notifier.process_events()
				if notifier.check_events():
					notifier.read_events()
				
			except Exception as e:
				print(e)
				notifier.stop()
					
		return False
	
	#def _inotify
	
	
	
	def _restore_groups_folders(self):
		
		t=threading.Thread(target=self.restore_groups_folders)
		t.daemon=True
		t.start()
		
	#def

	def add_user(self,plantille,properties,generic_mode=False):
		
		generated_user=None
		'''
		properties["uid"]=properties["uid"].encode("utf8")
		properties["cn"]=properties["cn"].encode("utf8")
		properties["sn"]=properties["sn"].encode("utf8")
		'''
		'''
		if "userPassword" in properties:
			properties["userPassword"]=properties["userPassword"].encode("utf8")
		'''
		
		if type(generic_mode)==type(True) and generic_mode:
			generated_user=self.ldap.add_user(generic_mode,plantille,properties)
		else:
			generated_user=self.ldap.add_user(False,plantille,properties)
		
		if type(generated_user) is dict:
			
			homepath = self.netfiles.exist_home_or_create(generated_user)
			if plantille=="Teachers" or plantille=="Others":
				self.pw.add_password(generated_user["uid"],generated_user["cn"],generated_user["sn"],generated_user["userPassword"])
			properties["group_type"]=plantille
			self.peter_pan.execute_python_dir('/usr/share/n4d/hooks/golem','add_user',properties)
			self.peter_pan.execute_python_dir('/usr/share/n4d/hooks/openmeetings','add_user',[properties])
			ret="true: " + generated_user["uid"]
			return n4d.responses.build_successful_call_response(ret)
		else:
			return n4d.responses.build_successful_call_response(generated_user)
		
	#def add_user
	

	def add_generic_users(self,plantille,group_type,number,generic_name,pwd_generation_type,pwd=None):
		
		generated_list=self.ldap.add_generic_users(plantille,group_type,number,generic_name,pwd_generation_type,pwd)
		for item in generated_list:
			#
			# Item {uid:name,userPassword:password}
			#
			
			homepath = self.netfiles.exist_home_or_create(item)
			
			#print "password saving..."
			if plantille=="Teachers" or plantille=="Others":
				self.pw.add_password(item["uid"],item["cn"],item["sn"],item["userPassword"])
			self.peter_pan.execute_python_dir('/usr/share/n4d/hooks/golem',('add_generic_users'),{'group':group_type,'user':item})

			properties = {}
			properties['group_type'] = plantille
			properties['uid'] = item['uid']
			properties['cn'] = item['uid']
			properties['sn'] = item['uid']
			self.peter_pan.execute_python_dir('/usr/share/n4d/hooks/openmeetings','add_user',[properties])
		
		return n4d.responses.build_successful_call_response(generated_list)
		
		
	#def add_generic_users
	
	def add_admin(self,user_name):
		# existing system user
	
		try:
			uid=pwd.getpwnam(user_name).pw_uid
			
			properties={}
			properties["uid"]=user_name
			properties["cn"]=user_name
			properties["sn"]=user_name
			properties["userPassword"]=uid
			properties["uidNumber"]=os.environ["SUDO_UID"]
			
			self.ldap.add_user(False,"Admin",properties)
			return True
			
		except Exception as e:
			
			return [False,e.message]
			
			
	
	#def add_admin
	
	def login(self,user_info):
		
		uid,password=user_info
		
		dic={}
		p = subprocess.Popen(["groups",uid],stdout = subprocess.PIPE,stderr = subprocess.PIPE)
		output = p.communicate()[0].decode("utf-8")
		output=output.replace("\n","")
		
		dic["groups"]=output
		
		students="ou=Students,ou=People," + self.llxvars("LDAP_BASE_DN")
		teachers="ou=Teachers,ou=People," + self.llxvars("LDAP_BASE_DN")
		admins="ou=Admins,ou=People," + self.llxvars("LDAP_BASE_DN")
		
		group_type="None"
		
		if output.find("students")!=-1:
			dic["path"]="uid=" + uid + "," + students
			group_type="students"
			
		if output.find("teachers")!=-1:
			dic["path"]="uid=" + uid + "," + teachers
			group_type="teachers"

		if output.find("admins")!=-1 and output.find("teachers")!=-1:
			dic["path"]="uid=" + uid + "," + teachers
			group_type="promoted-teacher"
		
		if output.find("adm")!=-1:
			dic["path"]="uid=" + uid + "," + admins
			group_type="admin"
			#return "true " + group_type

		'''
		if "NTicketsManager" in objects:
			if objects["NTicketsManager"].validate_user(uid,password):
				return "true " + group_type
		'''
		
		if self.core.validate_user(uid,password)["status"]==0:
			old_ret="true "+ group_type
		else:
			old_ret="false"
			
			
		return n4d.responses.build_successful_call_response(old_ret)

		
	#def login
	
	
	
	def change_own_password(self,user_info,new_password):
		
		uid,password=user_info
		dic={}
		p = subprocess.Popen(["groups",uid],stdout = subprocess.PIPE,stderr = subprocess.PIPE)
		output = p.communicate()[0].decode("utf-8")
		output=output.replace("\n","")
		
		dic["groups"]=output
		
		students="ou=Students,ou=People," + self.llxvars("LDAP_BASE_DN")
		teachers="ou=Teachers,ou=People," + self.llxvars("LDAP_BASE_DN")
		admin="ou=Admins,ou=People," + self.llxvars("LDAP_BASE_DN")
		others="ou=Other,ou=People," + self.llxvars("LDAP_BASE_DN")
		
		if output.find("students")!=-1:
			path="uid=" + uid + "," + students
		elif output.find("teachers")!=-1:
			path="uid=" + uid + "," + teachers
		elif output.find("others")!=-1:
			path="uid=" + uid + "," + others
		elif output.find("admin")!=-1:
			path="uid=" + uid + "," + admin
		else:
			return n4d.responses.build_failed_call_response("false")
		
		dic["path"]=path
		
		#dic["llxvars"]=llxvars
		
		try:
			tmp_ldap=ldap.initialize(self.llxvars("CLIENT_LDAP_URI"))
			dic["a"]="initialize"
			tmp_ldap.set_option(ldap.VERSION,ldap.VERSION3)
			dic["b"]="set_option"
			tmp_ldap.bind_s(path,password)
			dic["c"]="bind"
			self.ldap.change_password(path,new_password)
			dic["d"]="ldap password"
			
			if "Teachers" in path:
				self.pw.set_externally_modified(uid)
			
			return n4d.responses.build_successful_call_response("true")
			
		except Exception as inst:

			dic["exception"]=inst
			print(inst)
			return n4d.responses.build_failed_call_response("false")
		
	#def change_own_password
	
	
	def delete_student(self,uid,delete_data=True):
		
		user_info={}
		user_info["uid"]=uid
		user_info["profile"]="students"
	
		#self.unfreeze_user(uid)
	
	
		if delete_data==True:
			homepath = self.netfiles.delete_home(user_info)

		path="/home/%s"%uid
		if os.path.exists(path):
			shutil.rmtree(path)
		
		ret=self.ldap.delete_student(uid)
		
		self.peter_pan.execute_python_dir('/usr/share/n4d/hooks/golem','delete_student')
		properties = {}
		properties['uid'] = uid
		properties['group_type'] = 'Students'
		self.peter_pan.execute_python_dir('/usr/share/n4d/hooks/openmeetings','delete_user',[properties])
		
		return n4d.responses.build_successful_call_response(ret)
		
	#def delete_student

		
	def delete_teacher(self,uid,delete_data=True):

		user_info={}
		user_info["uid"]=uid
		user_info["profile"]="teachers"

		#self.unfreeze_user(uid)		

		if delete_data==True:
			homepath = self.netfiles.delete_home(user_info)

		path="/home/%s"%uid
		if os.path.exists(path):
			shutil.rmtree(path)
		
		self.pw.remove_password(uid)
		ret=self.ldap.delete_teacher(uid)
		
		self.peter_pan.execute_python_dir('/usr/share/n4d/hooks/golem','delete_teacher')
		properties = {}
		properties['uid'] = uid
		properties['group_type'] = 'Teachers'
		self.peter_pan.execute_python_dir('/usr/share/n4d/hooks/openmeetings','delete_user',[properties])
		
		return n4d.responses.build_successful_call_response(ret)
		
	#def delete_teacher


	def delete_other(self,uid,delete_data=True):

		user_info={}
		user_info["uid"]=uid
		user_info["profile"]="others"
		
		self.unfreeze_user(uid)
		
		
		if delete_data==True:
			homepath = self.netfiles.delete_home(user_info)

		self.pw.remove_password(uid)

		ret=self.ldap.delete_other(uid)
		self.peter_pan.execute_python_dir('/usr/share/n4d/hooks/golem','delete_other')
		properties = {}
		properties['uid'] = uid
		properties['group_type'] = 'Others'
		self.peter_pan.execute_python_dir('/usr/share/n4d/hooks/openmeetings','delete_user',[properties])

		return n4d.responses.build_successful_call_response(ret)
		
	#def delete_other


	def delete_students(self,delete_data=True):
		
		list=self.ldap.search_user("*")
		
		ret_list=[]
		
		for item in list:
			if item.properties["path"].find("ou=Students")!=-1:
				ret=self.delete_student(item.properties["uid"],delete_data)["return"]
				ret_list.append(item.properties["uid"] +":"+ret)
		
		
		self.ldap.set_xid("Students",20000)

		return n4d.responses.build_successful_call_response(ret_list)

	#def delete_students

	
	def delete_teachers(self,delete_data=True):
		
		list=self.ldap.search_user("*")
		
		ret_list=[]
		
		for item in list:
			if item.properties["path"].find("ou=Teachers")!=-1:
				ret=self.delete_teacher(item.properties["uid"],delete_data)["return"]
				ret_list.append(item.properties["uid"] +":"+ret)

		self.ldap.set_xid("Teachers",5000)

		return n4d.responses.build_successful_call_response(ret_list)
			
		
	#def delete_students
	

	def delete_all(self,delete_data=True):
		
		list=self.ldap.search_user("*")
		
		ok=True
		
		ret_list=[]
		
		for item in list:
			if item.properties["path"].find("ou=Teachers")!=-1:
				ret=self.delete_teacher(item.properties["uid"],delete_data)["return"]
				ret_list.append(item.properties["uid"] +":"+ret)
				
			if item.properties["path"].find("ou=Students")!=-1:
				ret=self.delete_student(item.properties["uid"],delete_data)["return"]
				ret_list.append(item.properties["uid"] +":"+ret)
				
			if item.properties["path"].find("ou=Other")!=-1:
				ret=self.delete_other(item.properties["uid"],delete_data)["return"]
				ret_list.append(item.properties["uid"] +":"+ret)
				
		self.ldap.set_xid("Students",20000)
		self.ldap.set_xid("Teachers",5000)
				
		return n4d.responses.build_successful_call_response(ret_list)
		
	#def delete_students


	def get_student_list(self):
		
		list=self.ldap.search_students("*")
		
		return_list=[]
		
		for item in list:
			return_list.append(item.properties)
							
		return n4d.responses.build_successful_call_response(return_list)
		
	def get_teacher_list(self):
		
		list=self.ldap.search_teachers("*")
		
		return_list=[]
		
		for item in list:
			return_list.append(item.properties)
							
		return n4d.responses.build_successful_call_response(return_list)
			
	def get_user_list(self,filter):

		list=self.ldap.search_user(filter)
		#return self.ldap.light_search(filter)
		
		return_list=[]
		for item in list:
			return_list.append(item.properties)
			
		return n4d.responses.build_successful_call_response(return_list)
		

	#def get_user_list
	
	def light_get_user_list(self):
		
		list=self.ldap.light_search()
		return n4d.responses.build_successful_call_response(list)
		
	#def light_get_user_list
	
	def get_available_groups(self):
		
		return n4d.responses.build_successful_call_response(self.ldap.get_available_groups())
		
	#def get_available_groups
	

	def add_to_group(self,uid,group):
		
		result=self.ldap.add_to_group_type(group,uid)
		user_info={}
		user_info["uid"]=uid
		try:
			path=self.ldap.get_dn(uid)
			
			if path.find("ou=Students")!=-1:
				user_info["profile"]="students"
			if path.find("ou=Teachers")!=-1:
				user_info["profile"]="teachers"	
			if path.find("ou=Other")!=-1:
				user_info["profile"]="others"	
				
			

			self.peter_pan.execute_python_dir('/usr/share/n4d/hooks/golem',('add_to_group'),{'group':{'cn':group},'user':user_info})
			#return must be "true" (string)
		except:
			pass
			
		return n4d.responses.build_successful_call_response(result)
		
	#def add_to_group
	
	def remove_from_group(self,uid,group):
		
		result=self.ldap.del_user_from_group(uid,group)
		user_info={}
		user_info["uid"]=uid
		
		
		
		#return must be "true" (string)

		self.peter_pan.execute_python_dir('/usr/share/n4d/hooks/golem',('remove_from_group'),{'group':{'cn':group},'user':user_info})
		return n4d.responses.build_successful_call_response(result)
		
	#def remove_from_group


	def change_student_personal_data(self,uid,name,surname):
		#name=unicode(name).encode("utf8")
		#surname=unicode(surname).encode("utf8")
		result=self.ldap.change_student_name(uid,name)
		result2=self.ldap.change_student_surname(uid,surname)
		if result==result2 and result=="true":
			
			# TODO
			# Execute hook to moodle


			properties = {}
			properties['group_type'] = 'Students'
			properties['uid'] = uid
			properties['cn'] = name
			properties['sn'] = surname
			self.peter_pan.execute_python_dir('/usr/share/n4d/hooks/openmeetings','update_user',[properties])

			return n4d.responses.build_successful_call_response(result)
		else:
			return n4d.responses.build_successful_call_response(result + "," + result2)
		
	#def change_personal_data
	
	def change_password(self,path,password,uid="",cn="",sn="",auto=False):
		
		#password=unicode(password).encode("utf8")
		result=self.ldap.change_password(path,password)
		
		#trying to obtain user uid
		list=path.split(",")
		uid=list[0].split("=")[1]
		
		
		#return=="true"
		
		if uid!="" and cn!="" and sn!="":
			self.pw.add_password(uid,cn,sn,password)
			
		if not auto:
			if "Teachers" in path:
				self.pw.set_externally_modified(uid)
		
		return n4d.responses.build_successful_call_response(result)
		
	#def change_student_password

	def change_student_password(self,uid,password):
		
		result=self.ldap.change_user_password(uid,password)
		
		#return=="true"
		
		
		return n4d.responses.build_successful_call_response(result)
		
	#def change_student_password
	def freeze_user(self,uid_list):
		self.ldap.freeze_user(uid_list)
		return n4d.responses.build_successful_call_response(0)
	#def freeze_user

	def freeze_group(self,cn):
		self.ldap.freeze_group(cn)
		return n4d.responses.build_successful_call_response(0)
	#def freeze_group

	def unfreeze_user(self,uid_list):
		self.ldap.unfreeze_user(uid_list)
		return n4d.responses.build_successful_call_response(0)
	#def unfreeze_user

	def unfreeze_group(self,cn):
		self.ldap.unfreeze_group(cn)
		return n4d.responses.build_successful_call_response(0)
	#def unfreeze_group
	
	def add_teacher_to_admins(self,uid):
		
		result=self.ldap.add_teacher_to_admins(uid)
		
		return n4d.responses.build_successful_call_response(result)
		
	#def add_teacher_to_admins
	
	def del_teacher_from_admins(self,uid):
		
		result=self.ldap.del_teacher_from_admins(uid)
		return n4d.responses.build_successful_call_response(result)
		
	#def de_teacher_from_admins
	
	
	def change_group_description(self,gid,description):
		
		#description=unicode(description).encode("utf8")
		result=self.ldap.change_group_description(gid,description)
		
		return n4d.responses.build_successful_call_response(result)
		
	#def change_group_description
	
	def delete_group(self,group_name):

		#self.unfreeze_group(gid)
		result=self.ldap.delete_group(group_name)
		try:
			self.netfiles.remove_group_folder(group_name)
		except Exception as e:
			print(e)
		
		self.peter_pan.execute_python_dir('/usr/share/n4d/hooks/golem',('delete_group'),{'group':{'cn':group_name}})
		return n4d.responses.build_successful_call_response(result)
		
	#def delete_group
	
	
	def add_group(self,properties):
		
		#properties["description"]=unicode(properties["description"]).encode("utf8")
		result=self.ldap.add_group(properties)
		
		try:
			self.create_group_folder(properties["cn"])
		except Exception as e:
			return n4d.responses.build_successful_call_response(result)
		
		try:
			self.peter_pan.execute_python_dir('/usr/share/n4d/hooks/golem',('add_group'),{'group':properties})
		except Exception as e:
			print(e)
		return n4d.responses.build_successful_call_response(result)
		
	#def add_group
	
	def get_students_passwords(self):
		
		slist = self.ldap.get_students_passwords()
		slist=self.quicksort(slist)
		return n4d.responses.build_successful_call_response(slist)
		
	#def get_students_passwords

	def get_teachers_passwords_encrypted(self):

		tlist= self.ldap.get_teachers_passwords()

		return n4d.responses.build_successful_call_response(self.quicksort(tlist))

	#def get_teachers_passwords_encrypted
	
	
	def get_teachers_passwords(self):

		ret=self.ldap.get_teachers_passwords()
		tmp_teachers={}
		for teacher in ret:
			tmp_teachers[teacher["uid"]]=teacher
				
				
		ret2=self.quicksort(self.pw.get_passwords())

		final_ret=[]
		for item in ret2:
			if item["uid"] in tmp_teachers:
				tmp_teachers[item["uid"]]["passwd"]=item["passwd"]
			

		for item in tmp_teachers:
			final_ret.append(tmp_teachers[item])
			
		return n4d.responses.build_successful_call_response(self.quicksort(final_ret))
		
	#def get_teachers_passwords
	
	
	def get_all_passwords(self,force_teachers=False):
		
		slist=self.ldap.get_students_passwords()
		list2=self.get_teachers_passwords()["return"]

		for item in list2:
			slist.append(item)

		return n4d.responses.build_successful_call_response(self.quicksort(slist))
		
	#def get_all_passwords
	
	def quicksort (self,lista): 
		self.sort_quicksort(lista,0,len(lista)-1) 
		return lista
	
	#def quicksort
	
	def sort_quicksort (self,lista,izdo,dcho) : 
		if izdo<dcho : 
			pivote=lista[int((izdo+dcho)/2)] 
			i,d=izdo,dcho 
			while i<=d : 
				while lista[i]['sn'].lower()<pivote['sn'].lower() : i+=1 
				while lista[d]['sn'].lower()>pivote['sn'].lower() : d-=1 
				if i<=d : 
					lista[i],lista[d]=lista[d],lista[i] 
					i+=1 
					d-=1 
			if izdo<d : self.sort_quicksort(lista,izdo,d) 
			if i<dcho : self.sort_quicksort(lista,i,dcho) 
		return lista
	#def sort_quicksort
	
	
	def generic_student_to_itaca(self,uid,nia):
		
		return n4d.responses.build_successful_call_response(self.ldap.generic_student_to_itaca(uid,nia))
		
	#def generic_student_to_itaca
	
	def generic_teacher_to_itaca(self,uid,nif):
		
		return n4d.responses.build_successful_call_response(self.ldap.generic_teacher_to_itaca(uid,nif))
		
	#def generic_teachers_to_itaca
	
	def send_xml_to_server(self,data64,file_name,passwd=""):
		server_path="/tmp/" + file_name
		try:
			ret=self.file_operations.send_file_to_server(data64,server_path)
			if self.mime.file(server_path).split(";")[0]=="application/xml":
				pass
			elif self.mime.file(server_path).split(";")[0]=="application/octet-stream":
				# some itaca files have bad character encryption and are detected as data stream
				# so we give the file yet another chance to be a valid xml file
				f=open(server_path)
				line=f.readline()
				f.close()
				is_xml=False
				if line.startswith("<?xml version"):
					# smells like an xml file? let's give it a chance
					is_xml=True

				if passwd=="" and not is_xml:
					return n4d.responses.build_successful_call_response("false:xml_encrypted")
				elif passwd!="" and not is_xml:
					p=subprocess.Popen(["openssl","enc","-des","-d","-k",passwd,"-in",server_path,"-out",server_path+".xml"],stderr=subprocess.PIPE)
					output=p.communicate()[1].decode("utf-8")
					if output!=None:
						if "bad decrypt" in output:
							return n4d.responses.build_successful_call_response("false:xml_bad_password")

					server_path=server_path+".xml"
					if self.mime.file(server_path).split(";")[0]=="application/xml":
						pass
					else:
						return n4d.responses.build_successful_call_response("false:invalid_xml")
						
			
		except Exception as e:
			print(e)
			return n4d.responses.build_successful_call_response("false:send_error")
		if ret==1:
			try:
				ret=self.gescen_set_path(server_path)
				if ret==True:
					return n4d.responses.build_successful_call_response("true")
				elif ret==False:
					return n4d.responses.build_successful_call_response("false:xml_error")
				elif ret=="false:xml_encrypted":
					return n4d.responses.build_successful_call_response(ret)
				else:
					return n4d.responses.build_successful_call_response("false:unknown_error")
			except:
				return n4d.responses.build_successful_call_response("false:xml_error")
		else:
			return n4d.responses.build_successful_call_response("false:send_error")
		
		
	#def send_xml_to_server
	
	
	def gescen_info(self):
		#as is
		return self.itaca.get_info()
	#def gescen_info
	
	def gescen_set_path(self,path):
		#as is
		return self.itaca.set_path(path)
	#def gescen_info
	
	def gescen_load(self):
		#as is
		return self.itaca.load_file()
	#def gescen_info

	def gescen_groups(self):
		return n4d.responses.build_successful_call_response(self.itaca.get_groups())
	#def gescen_group

	def gescen_partial(self,group_list):
		#print "partial"
		#print group_list
		self.sharefunctions['generate_uid'] = generate_uid
		users_added = self.itaca.partial_import(group_list)
		self.peter_pan.execute_python_dir('/usr/share/n4d/hooks/golem',('gescen_partial'),{})
		self.peter_pan.execute_python_dir('/usr/share/n4d/hooks/openmeetings','add_user',users_added)
		return n4d.responses.build_successful_call_response('true')

	#def gescen_partial

	def gescen_full(self):

		try:
			self.sharefunctions['generate_uid'] = generate_uid
		except Exception as e:
			print(e)
			n4d.responses.build_failed_call_response()

		ret,users_added=self.itaca.full_import()
		self.peter_pan.execute_python_dir('/usr/share/n4d/hooks/golem',('gescen_full'),{})
		self.peter_pan.execute_python_dir('/usr/share/n4d/hooks/openmeetings','add_user',users_added)
		return n4d.responses.build_successful_call_response(ret)
	#def gescen_full
	
	def empty_students(self,generic=None):
		list=self.ldap.search_user("*")
		
		ret_list=[]
		
		for item in list:
			if item.properties["path"].find("ou=Students")!=-1:
				ret=self.empty_home(item.properties)["return"]
				ret_list.append(item.properties["uid"] +":"+ret)
		return n4d.responses.build_successful_call_response(ret_list)
	#def empty_students
	
	def empty_teachers(self,generic=None):
		list=self.ldap.search_user("*")
		
		ret_list=[]
		
		for item in list:
			if item.properties["path"].find("ou=Teachers")!=-1:
				ret=self.empty_home(item.properties)["return"]
				ret_list.append(item.properties["uid"] +":"+ret)
		return n4d.responses.build_successful_call_response(ret_list)
	#def empty_teachers
	
	def empty_others(self,generic=None):
		list=self.ldap.search_user("*")
		
		ret_list=[]
		
		for item in list:
			if item.properties["path"].find("ou=Other")!=-1:
				ret=self.empty_home(item.properties)["return"]
				ret_list.append(item.properties["uid"] +":"+ret)
		return n4d.responses.build_successful_call_response(ret_list)
	#def empty_others
	
	def empty_all(self):
		
		ret_list=[]
		ret_list.extend(self.empty_students(True)["return"])
		ret_list.extend(self.empty_teachers(True)["return"])
		ret_list.extend(self.empty_others(True)["return"])
		return n4d.responses.build_successful_call_response(ret_list)
		
	#def empty_all
		
		
	
	def empty_home(self,user_info):
		try:
			self.netfiles.delete_home(user_info)
			self.netfiles.create_home(user_info)
			return n4d.responses.build_successful_call_response("true")
		except:
			return n4d.responses.build_successful_call_response("false")
	#def empty_home

	def get_frozen_users(self):
		return n4d.responses.build_successful_call_response(self.ldap.get_frozen_users())
	#def get_frozen_users

	def get_frozen_groups(self):
		return n4d.responses.build_successful_call_response(self.ldap.get_frozen_groups())
	#def get_frozen_groups
	
	def is_frozen_user(self,user):
		return n4d.responses.build_successful_call_response(self.ldap.is_frozen_user(user))
		
	def exist_home_or_create(self,user):
		return n4d.responses.build_successful_call_response(self.netfiles.exist_home_or_create(user))
		

	def create_group_folder(self,group_name):
		
		return n4d.responses.build_successful_call_response(self.netfiles.create_group_folder(group_name))
		
		
	#def create_group_folder
	
	def restore_groups_folders(self):
		ret=[]
		try:
			
			for item in self.get_available_groups():
				try:
					id=self.create_group_folder(item["cn"][0])["return"]
					ret.append((item["cn"][0],id))
				except Exception as ex:
					ret.append((item["cn"][0],str(ex)))
			
		except Exception as e:
			ret.append(str(e))
			
		return n4d.responses.build_successful_call_response(ret)
		
	#def restore_group_folders
	
	def full_search(self):
		
		return n4d.responses.build_successful_call_response(self.ldap.full_search("*"))
		
	#def full_search
	
	
	def export_llum_info(self):
		
		try:
			
			user_list=self.get_user_list("*")["return"]
			slist=self.get_students_passwords()["return"]
			tlist=self.get_teachers_passwords_encrypted()["return"]
			pwd_list=self.quicksort(slist+tlist)
			groups=self.get_available_groups()["return"]
			exported_groups={}
			exported_users={}
		
			for item in groups:
				
				exported_groups[item["cn"][0]]={}
				if "memberUid" in item:
					exported_groups[item["cn"][0]]["members"]=item["memberUid"]
				else:
					exported_groups[item["cn"][0]]["members"]=[]
				exported_groups[item["cn"][0]]["description"]=item["description"][0]
		
			for item in user_list:
				
				if item["profile"]=="teachers":
					profile="Teachers"
				elif item["profile"]=="students":
					profile="Students"
				else:
					continue
				exported_users[item["uid"]]={}
				exported_users[item["uid"]]["profile"]=profile
				exported_users[item["uid"]]["cn"]=item["cn"]
				exported_users[item["uid"]]["sn"]=item["sn"]
				exported_users[item["uid"]]["groups"]=item["groups"]
				exported_users[item["uid"]]["is_admin"]=item["is_admin"]
				exported_users[item["uid"]]["uidNumber"]=item["uidNumber"]
				if "x-lliurex-usertype" in item:
					exported_users[item["uid"]]["x-lliurex-usertype"]=item["x-lliurex-usertype"]
				else:
					exported_users[item["uid"]]["x-lliurex-usertype"]="generic"
					
				if "x-lliurex-nia" in item:
					exported_users[item["uid"]]["x-lliurex-nia"]=item["x-lliurex-nia"]
				if "x-lliurex-nif" in item:
					exported_users[item["uid"]]["x-lliurex-nif"]=item["x-lliurex-nif"]

			for item in pwd_list:
				if item["uid"] in exported_users:
					exported_users[item["uid"]]["userPassword"]=item["passwd"]
					exported_users[item["uid"]]["sambaNTPassword"]=item["sambaNTPassword"]
					exported_users[item["uid"]]["sambaLMPassword"]=item["sambaLMPassword"]
				

			tmp_pwd=self.get_teachers_passwords()["return"]

			for teacher in tmp_pwd:
				if teacher["uid"] in exported_users:
					exported_users[teacher["uid"]]["known_password"]=teacher["passwd"]

			exported={}
			exported["groups"]=exported_groups
			exported["users"]=exported_users

			return n4d.responses.build_successful_call_response([True,exported])
		
		except Exception as e:
			print(e)
			return n4d.responses.build_successful_call_response([False,str(e)])
		
						
		
	#def export_llum_info
	
	
	def import_llum_info(self,exported_info):
	
		def sort_users_by_uidNumber(dic_a):
		
						
			new_dic={}
			new_dic["groups"]=dic_a["groups"]
			new_dic["users"]={}
			new_dic["skipped_users"]={}
			for user in dic_a["users"]:
				
				try:
					uidn=int(dic_a["users"][user]["uidNumber"])
					dic_a["users"][user]["uid"]=user
					if uidn not in new_dic["users"]:
						new_dic["users"][uidn]=dic_a["users"][user]
					else:
						if "uidNumber" in dic_a["users"][user]:
							dic_a["users"][user].pop("uidNumber")
						new_dic["skipped_users"][user]=dic_a["users"][user]
					
				except Exception as e:
					continue
				
			return new_dic
			
		#def sort_users_by_uidNumber
		
		
		exported_info=sort_users_by_uidNumber(exported_info)

				
		skipped=[]
		skipped_uidn=[]
		
		try:
			for group in exported_info["groups"]:

				properties={}
				properties["description"]=exported_info["groups"][group]["description"]
				properties["cn"]=group
				print("Adding group %s..."%group)
				self.add_group(properties)
				
			for uidn in sorted(exported_info["users"]):

				user=exported_info["users"][uidn]["uid"]
				uids={}
				for key in self.ldap.xid_counters:
					uids[key]=int(self.ldap.xid_counters[key])

				properties={}
				properties["uid"]=user
				properties["cn"]=exported_info["users"][uidn]["cn"]
				properties["sn"]=exported_info["users"][uidn]["sn"]
				properties["userPassword"]=exported_info["users"][uidn]["userPassword"]
				properties["sambaLMPassword"]=exported_info["users"][uidn]["sambaLMPassword"]
				properties["sambaNTPassword"]=exported_info["users"][uidn]["sambaNTPassword"]
				
				if "uidNumber" in exported_info["users"][uidn]:
					properties["uidNumber"]=exported_info["users"][uidn]["uidNumber"]

				if "x-lliurex-usertype" in exported_info["users"][uidn]:
					properties["x-lliurex-usertype"]=exported_info["users"][uidn]["x-lliurex-usertype"]
				else:
					properties["x-lliurex-usertype"]="generic"
					
				if "x-lliurex-nia" in exported_info["users"][uidn]:
					properties["x-lliurex-nia"]=exported_info["users"][uidn]["x-lliurex-nia"]
				if "x-lliurex-nif" in exported_info["users"][uidn]:
					properties["x-lliurex-nif"]=exported_info["users"][uidn]["x-lliurex-nif"]

				profile=exported_info["users"][uidn]["profile"]

				if int(uids[profile]) > int(properties["uidNumber"]) :
					#print("Skipping %s ..."%user)
					skipped.append(user)
					continue

				self.ldap.set_xid(profile,properties["uidNumber"])
				uids[profile]=properties["uidNumber"]
				self.ldap.xid_counters[profile]=str(uids[profile])
				
				#print("Adding user %s..."%user)
				ret=self.add_user(profile,properties)
				
				if "true" in str(ret):
					if "uidNumber" in properties:
						if int(uids[profile]) < int(properties["uidNumber"]):
							uids[profile]=int(properties["uidNumber"])
							
					if profile=="Teachers":
						if "known_password" in exported_info["users"][uidn]:
							password=exported_info["users"][uidn]["known_password"]
						else:	
							password=properties["userPassword"]

						if "{SSHA}" in password:
							password="#! UNKNOWN PASSWORD !#"
							
						self.pw.add_password(properties["uid"],properties["cn"],properties["sn"],password)


			# Adding skipped users with new uidnumber
			
			# part 1: those skipped because they already had conflicting uids in llum file
			
			for user in exported_info["skipped_users"]:
				
				properties={}
				properties["uid"]=user
				properties["cn"]=exported_info["skipped_users"][user]["cn"]
				properties["sn"]=exported_info["skipped_users"][user]["sn"]
				properties["userPassword"]=exported_info["skipped_users"][user]["userPassword"]
				properties["sambaLMPassword"]=exported_info["skipped_users"][user]["sambaLMPassword"]
				properties["sambaNTPassword"]=exported_info["skipped_users"][user]["sambaNTPassword"]
				if "x-lliurex-usertype" in exported_info["skipped_users"][user]:
					properties["x-lliurex-usertype"]=exported_info["skipped_users"][user]["x-lliurex-usertype"]
				else:
					properties["x-lliurex-usertype"]="generic"
				profile=exported_info["skipped_users"][user]["profile"]
				
				
				#without uidNumber, add_user should automatically get the next one
				#print("Trying to add skipped.1 user %s..."%user)
				ret=self.add_user(profile,properties)
				
				if "true" in str(ret):

					if profile=="Teachers":
						if "known_password" in exported_info["skipped_users"][user]:
							password=exported_info["skipped_users"][user]["known_password"]
						else:	
							password=properties["userPassword"]

						if "{SSHA}" in password:
							password="#! UNKNOWN PASSWORD !#"
							
						self.pw.add_password(properties["uid"],properties["cn"],properties["sn"],password)

					uidn=self.ldap.xid_counters[profile]
					properties["uidNumber"]=uidn
					properties["profile"]=profile.lower()
					
					# llum already calls regenerate files function afterwards
					#self.exist_home_or_create(properties)
			
			# part 2: those who couldnt be added because there was already another user with that uidNumber

			for uidn in skipped_uidn:
				
				user=exported_info["users"][uidn]["uid"]
				
				properties={}
				properties["uid"]=user
				properties["cn"]=exported_info["users"][uidn]["cn"]
				properties["sn"]=exported_info["users"][uidn]["sn"]
				properties["userPassword"]=exported_info["users"][uidn]["userPassword"]
				properties["sambaLMPassword"]=exported_info["users"][uidn]["sambaLMPassword"]
				properties["sambaNTPassword"]=exported_info["users"][uidn]["sambaNTPassword"]
				if "x-lliurex-usertype" in exported_info["users"][uidn]:
					properties["x-lliurex-usertype"]=exported_info["users"][uidn]["x-lliurex-usertype"]
				else:
					properties["x-lliurex-usertype"]="generic"
				
				profile=exported_info["users"][uidn]["profile"]
				'''
				properties["uidNumber"]=self.ldap.xid_counters[profile]
				uids[profile]=properties["uidNumber"]
				exported_info["users"][uidn]["uidNumber"]=properties["uidNumber"]
				'''
				
				#without uidNumber, add_user should automatically get the next one
				#print("Trying to add skipped.2 user %s..."%user)
				ret=self.add_user(profile,properties)

				if "true" in str(ret):
					'''
					if "uidNumber" in properties:
						if uids[profile] < int(properties["uidNumber"]):
							uids[profile]=int(properties["uidNumber"])
					'''
					if profile=="Teachers":
						if "known_password" in exported_info["users"][uidn]:
							password=exported_info["users"][uidn]["known_password"]
						else:	
							password=properties["userPassword"]

						if "{SSHA}" in password:
							password="#! UNKNOWN PASSWORD !#"
							
						self.pw.add_password(properties["uid"],properties["cn"],properties["sn"],password)
						
					uidn=self.ldap.xid_counters[profile]
					properties["uidNumber"]=uidn
					properties["profile"]=profile.lower()
					
					# llum already calls regenerate files function afterwards
					#self.exist_home_or_create(properties)
					skipped.remove(user)
				
				
			for group in exported_info["groups"]:
			
				for i in exported_info["groups"][group]["members"]:
					try:
						if i not in skipped:
							#print("Adding user %s to group %s..."%(i,group))
							self.add_to_group(i,group)
					except Exception as e:
						print(e)
						pass
						
					
			for uidn in exported_info["users"]:
				
				if exported_info["users"][uidn]["is_admin"]:
					self.add_teacher_to_admins(user)
					
			for user in exported_info["skipped_users"]:
				
				if exported_info["skipped_users"][user]["is_admin"]:
					self.add_teacher_to_admins(user)
					
					
			return n4d.responses.build_successful_call_response([True,])
			
		except Exception as e:
			print(e)
			return n4d.responses.build_successful_call_response([False,str(e)])
		
	#def import_llum_info
	
	def regenerate_net_files(self,mode=0):
		
		try:
			ret=self.light_get_user_list()
			users=[]
			for item in ret:
				user={}
				user["profile"]=item[5]
				user["uid"]=item[1]
				user["uidNumber"]=item[2]
				users.append(user)
			
			for user in users:
				try:
					self.netfiles.exist_home_or_create(user,mode)
				except:
					pass
				
			try:
				
				self.restore_groups_folders()
			except:
				pass
				
			return n4d.responses.build_successful_call_response()
			
		except:
			n4d.responses.build_failed_call_response()
		
	#def regenerate_net_files
	
	def is_roadmin_available(self):
		
		try:
			return n4d.responses.build_successful_call_response(self.ldap.custom_search("cn=roadmin,"+self.llxvars("LDAP_BASE_DN"))["status"])
		except:
			return n4d.responses.build_successful_call_response(False)
	
	#def is_roadmin_avaiable
	

#class Golem


if __name__=="__main__":
	
	golem=Golem()
