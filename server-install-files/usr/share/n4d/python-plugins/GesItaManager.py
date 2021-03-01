# coding=utf-8
import ldap
import subprocess
import xml.etree
import xml.etree.ElementTree
import os

class GrupGes:
	def __init__(self):
		self.attributes = {}
		self.memmbers = []
	#def __init__
	
class UserGes:
	def __init__(self):
		self.attributes = {}
	#def __init__



class GesItaManager:
	
	def __init__(self,llxvar,golem,filepath = None):
		self.llxvar = llxvar
		self.golem = golem
		self.info = {}
		self.students = []
		self.teachers = []
		self.groups = {}
		self.usersfordelete = {}
		#This is the last function
		self.set_path(filepath)
		self.users_added = []
	#def __init__
	
	def set_path(self,filepath):
		if filepath != None:
			if os.path.exists(filepath):
				self.filepath = filepath
				return self.load_file()
			return False
		return False
	#def set_path
	
	def load_file(self):

		if self.filepath != None:
			self.info = {}
			self.students = []
			self.teachers = []
			self.groups = {}
			self.usersfordelete = {}
			document=xml.etree.ElementTree.parse(self.filepath)
			root = document.getroot()
			for keyattrib,valattrib in root.attrib.items():
				if valattrib != None:
					self.info[keyattrib] = valattrib.encode('utf-8')

			listofgroups = root.find("grups")
			if listofgroups != None:
				for group in listofgroups:
					auxgroup = GrupGes()
					for auxattrib in group:
						if auxattrib.text != None:
							auxgroup.attributes[auxattrib.tag] = auxattrib.text.encode('utf-8')
					self.groups[auxgroup.attributes['codi']] = auxgroup
			
			self.groups["sense_grup"] = GrupGes()
			self.groups["sense_grup"].attributes["codi"]="sense_grup"
			self.groups["sense_grup"].attributes["nom"]="ALUMNES SENSE GRUP"
			
			listofstudents = root.find("alumnes")
			if listofstudents != None:
				for student in listofstudents:
					auxuser = UserGes()
					for auxattrib in student:
						if auxattrib.text != None:
							auxuser.attributes[auxattrib.tag] = auxattrib.text.encode('utf-8')
					self.students.append(auxuser)
					try:
							self.groups[auxuser.attributes['grup']].memmbers.append(auxuser)
					
					except Exception as e:
							auxuser.attributes["grup"]="sense_grup"
							self.groups["sense_grup"].memmbers.append(auxuser)
				

							
							
			listofteachers = root.find("professors")
			if listofteachers != None:
				for teacher in listofteachers:
					auxuser = UserGes()
					for auxattrib in teacher:
						if auxattrib.text != None:
							auxuser.attributes[auxattrib.tag] = auxattrib.text.encode('utf-8')
					self.teachers.append(auxuser)
			return True
		return False
					
	#def load_file
	
	def get_info(self):
		
		return self.info
		
	#def get_info
	
	def get_groups(self):
		result = []
		for group in self.groups:
			result.append(group)
		return result
	#def get_groups
	
	def partial_import(self,listgroups):
		self.users_added = []
		itacagroups = self.get_groups()
		for groupname in listgroups:
			if groupname in itacagroups:
				listofusers = self.groups[groupname].memmbers
				prop = {}
				prop['cn'] = groupname
				prop['description'] = self.groups[groupname].attributes['nom']
				prop['x-lliurex-grouptype'] = 'itaca'
				self.golem.ldap.add_group(prop)
				#
				# OLD CREATE GROUP FOLDER WAS HERE
				#
				self.golem.peter_pan.execute_python_dir('/usr/share/n4d/hooks/gesitamanager',('add_group'),{'group':prop})
				for user in listofusers:
					self.insert_user(user,'Students')
		for teacher in self.teachers:
			self.insert_user(teacher,'Teachers')
			
		try:
			self.golem.restore_groups_folders()
		except:
			pass
		for user in self.users_added:
			user['group_type'] = user['profile'].capitalize()
		return self.users_added
		
	#def partial_import
			
	def full_import(self,best_effort=True):
		filter = "(|(x-lliurex-usertype=itaca)(x-lliurex-usertype=gescen))"
		self.users_added = []
		try:
			self.usersfordelete = self.golem.ldap.search_user_with_filter(filter)
		except Exception as e:
			print(e)
			raise e
		
		for nomgroup,group in self.groups.items():
			#if group exist on ldap do anything
			prop = {}
			prop['cn'] = group.attributes['codi']
			prop['description'] = group.attributes['nom']
			prop['x-lliurex-grouptype'] = 'itaca'
		
			self.golem.ldap.add_group(prop)
			self.golem.peter_pan.execute_python_dir('/usr/share/n4d/hooks/gesitamanager',('add_group'),{'group':prop})
			

		for student in self.students:
			try:
				self.insert_user(student,'Students')
			except Exception as e:
				print("[!] Failed to import " + str(student.attributes) + " due to " + str(e))
				if not best_effort:
					raise e
				
			
		for teacher in self.teachers:
			try:
				self.insert_user(teacher,'Teachers')
			except Exception as e:
				print("[!] Failed to import " + str(teacher.attributes) + " due to " + str(e))
				if not best_effort:
					raise e
			
			
		try:
			self.golem.restore_groups_folders()
		except:
			pass
		
		for user in self.users_added:
			user['group_type'] = user['profile'].capitalize()
	
		return self.usersfordelete,self.users_added
	#def full_import
		
	def insert_user(self,user,typeuser):
		
		listuser = []
		typefilter = ""
		nia = ""
		nif = ""
		
		if 'nif' in user.attributes and len(user.attributes['nif']) > 0:
			nif = user.attributes['nif']
			filter = "(x-lliurex-nif="+nif+")"
			listuser = self.golem.ldap.search_user_with_filter(filter)
			typefilter = "nif"
		elif 'nia' in user.attributes and len(user.attributes['nia']) > 0:
			nia = user.attributes['nia']
			filter = "(x-lliurex-nia="+nia+")"
			listuser = self.golem.ldap.search_user_with_filter(filter)
			typefilter = "nia"
		elif 'numeroExpedient' in user.attributes and len(user.attributes['numeroExpedient']) > 0:
			lliurexrecord = user.attributes['numeroExpedient']
			filter = "(x-lliurex-record="+lliurexrecord+")"
			listuser = self.golem.ldap.search_user_with_filter(filter)
			typefilter = "record"
		
		if len(listuser) == 0:
			filter = "(&(cn="+user.attributes['nom']+")(sn="+user.attributes['cognoms']+"))"
			listuser = self.golem.ldap.search_user_with_filter(filter)
			typefilter = "name and surname"
		
		if len(listuser) == 0:
		
			#
			#	User not exist on Ldap. Create new user
			#

			if 'uid' in user.attributes and len(user.attributes['uid']) >0:
				useruid=user.attributes['uid']
			else:
				useruid = self.golem.sharefunctions['generate_uid'](user.attributes['nom'].decode('utf-8'),user.attributes['cognoms'].decode('utf-8'))
		
			#Create user
			prop={}
			prop['uid'] = useruid
			prop['cn'] = user.attributes['nom']
			prop['sn'] = user.attributes['cognoms']
			if 'numeroExpedient' in user.attributes:
				prop['x-lliurex-record'] = user.attributes['numeroExpedient']
		
			if typeuser == 'Students':
				if 'nif' in user.attributes:
					prop['x-lliurex-nif'] = user.attributes["nif"]
					prop['x-lliurex-usertype'] = 'gescen'

				if 'nia' in user.attributes:
					prop['x-lliurex-nia'] = user.attributes["nia"]
					prop['x-lliurex-usertype'] = 'itaca'
				else:
					prop['x-lliurex-usertype'] = 'gescen'
			else:
				prop['x-lliurex-usertype'] = 'itaca'
				if 'nif' in user.attributes:
					prop['x-lliurex-nif'] = nif
		
			if "password" in user.attributes and  len(user.attributes['password']) > 0:
				prop["userPassword"]=user.attributes['password']
			
			try:
				user_list=self.golem.ldap.search_user(prop["uid"])
		
				if len(user_list)>0:
					inserteduser = self.golem.ldap.add_user(True,typeuser,prop)
				else:
					inserteduser= self.golem.ldap.add_user(False,typeuser,prop)

			except Exception as e:
				print(e)
				return False
				
			
			self.golem.netfiles.create_home(inserteduser)
			
			if typeuser == 'Students':
				#Join to group
				self.golem.ldap.add_to_group_type(user.attributes['grup'],inserteduser['uid'])
				
				self.golem.peter_pan.execute_python_dir('/usr/share/n4d/hooks/gesitamanager',('join_group'),{'group':{'cn':user.attributes['grup']},'user':inserteduser})
			#Write password in file
			if typeuser == 'Teachers':
				self.golem.pw.add_password(inserteduser["uid"],inserteduser['cn'],inserteduser['sn'],inserteduser["userPassword"])
			self.users_added.append(inserteduser)
			return {"status":True,"msg":"New entry",}
		else:
			#
			# User exist on system. Update parameters
			#
			
			if len(listuser) > 1:
				return {"status":False,"msg":"Duplicated " + typeuser}
			else:
				aux = listuser.keys()[0]
				upgradeuser = listuser[aux]
				
				if typeuser == 'Students':
					
					groups = self.golem.ldap.get_groups(upgradeuser['uid'])
					for auxgroup in groups:
						
						self.golem.ldap.del_user_from_group(upgradeuser['uid'],auxgroup)
						
						
						self.golem.peter_pan.execute_python_dir('/usr/share/n4d/hooks/gesitamanager',('drop_group'),{'group':{'cn':auxgroup},'user':upgradeuser})
					
					self.golem.netfiles.exist_home_or_create(upgradeuser)
					self.golem.ldap.add_to_group_type(user.attributes['grup'],upgradeuser['uid'])
					self.golem.peter_pan.execute_python_dir('/usr/share/n4d/hooks/gesitamanager',('join_group'),{'group':{'cn':user.attributes['grup']},'user':upgradeuser})
					
				try:
					self.usersfordelete.pop(upgradeuser['uid'])
				except Exception as exce:
					return {"status":True,"msg":"Error on search user " + upgradeuser['uid'] + " in Ldap"}
				
				return {"status":True,"msg":"Update user"}
	
	#def insert_user
