# -*- coding: utf-8 -*-
import sys
import os
import tarfile
import tempfile
import time
import configparser as ConfigParser

import n4d.server.core
import n4d.responses
import n4d.utils

class ServerBackupManager:
	
	RESTORE_ERROR=-10
	RESTORE_FILE_NOT_FOUND_ERROR=-15
	RESTORE_UNKNOWN_ERROR=-30
	
	FINAL_OPERATIONS_ERROR=-50

	def __init__(self):
		
		self.backup_list=["VariablesManager","Hostname","NetworkManager","Dnsmasq","N4dProxy","SlapdManager","PamnssPlugin","SambaManager"]
		#self.backup_list=["VariablesManager","Hostname","NetworkManager","Dnsmasq","N4dProxy","SlapdManager","PamnssPlugin","SambaManager","NetFoldersManager","MysqlManager","CupsManager","ApacheManager"]
		self.core=n4d.server.core.Core.get_core()
		
	#def init

	def backup(self,path=None,service_list=None,netfolders_list=None):
		
		return self.server_basics_backup(path,service_list,netfolders_list)
		
	#def backup
	
	def get_basic_services_list(self):
		
		return self.backup_list
		
	#def get_basic_services_list
		
	
	def server_basics_backup(self,path=None,service_list=None,netfolders_list=None):


		if service_list==None:
			service_list=self.backup_list
		
		if path==None:
			cur_date=time.strftime("%d%m%Y")
			path="/backup/%s"%cur_date
			if not os.path.exists(path):
				os.makedirs(path)
		
		if os.path.exists(path):
			
			file_name=path+"/"+n4d.utils.get_backup_name("ServerBackup")
			tar=tarfile.open(file_name,"w:gz")
			
			f=open(path+"/backup_files.conf","w")
			f.write("[ServerBackupManager]\n")
			
			ret={}
			for service in service_list:
				try:

					if service=="NetFoldersManager":
						#ret[service]=objects[service].backup(netfolders_list,path)
						tmp=self.core.get_plugin(service).backup(netfolders_list,path)["return"]
						if tmp["status"]==0:
							ret[service]=tmp["return"]
						else:
							e=Exception(tmp["msg"])
							raise e
					
					elif service=="VariablesManager":
						tmp=self.core.variables_manager.backup(path)
						if tmp["status"]==0:
							ret[service]=tmp["return"]
						else:
							e=Exception(tmp["msg"])
							raise e
					
					else:
						tmp=self.core.get_plugin(service).backup(path)
						if tmp["status"]==0:
							ret[service]=tmp["return"]
						else:
							e=Exception(tmp["msg"])
							raise e
						
					if ret[service][0]:
						fname=ret[service][1].split("/")[-1]
						tar.add(ret[service][1],arcname=fname)
						f.write("%s=%s\n"%(service,fname))
						os.remove(ret[service][1])	
			
				except Exception as e:
					ret[service]=[False,str(e)]
					f.write("# [!] %s FAILED: %s\n"%(service,str(e)))
				
		
			f.close()
			
			os.system("lliurex-version -n > %s/lliurex-version"%path)
			tar.add(path+"/backup_files.conf",arcname="backup_files.conf")
			tar.add(path+"/lliurex-version",arcname="lliurex-version")
			os.remove(path+"/backup_files.conf")
			os.remove("%s/lliurex-version"%path)
			tar.close()
			
			os.system("chmod 660 %s"%file_name)
			os.system("chown root:admins %s"%file_name)
			
			ret=[True,ret,file_name]
			return n4d.responses.build_successful_call_response(ret)
			
		else:
			ret=[False,ret,"Backup file not found"]
			return n4d.responses.build_failed_call_response(ret)
		
	#def backup
	
	def restore(self,file_name):
		
		return self.server_basics_restore(file_name)
	
	def server_basics_restore(self,file_name):
		
		if os.path.exists(file_name):
		
			tmp_dir=tempfile.mkdtemp()
			tar=tarfile.open(file_name,"r")
			tar.extractall(tmp_dir)
			tar.close()
			if os.path.exists(tmp_dir+"/backup_files.conf"):
				try:
					cfg=ConfigParser.ConfigParser()
					cfg.optionxform=str
					cfg.read(tmp_dir+"/backup_files.conf")
					ret={}
					
					self.restoring_version=None
				
					if os.path.exists(tmp_dir+"/lliurex-version"):
						f=open(tmp_dir+"/lliurex-version")
						self.restoring_version=f.readline().strip("\n")
						self.restoring_version=".".join(self.restoring_version.split(".")[0:2])
					for items in cfg.items("ServerBackupManager"):
						key,value=items
						try:
							if key=="VariablesManager":
								tmp=self.core.variables_manager.restore(tmp_dir+"/"+value)
								if tmp["status"]==0:
									ret[key]=[True,""]
								else:
									ret[key]=[False,ret["msg"]]
								
							elif self.core.is_plugin_available(key):
								tmp=self.core.get_plugin(key).restore(tmp_dir+"/"+value)
								if tmp["status"]==0:
									ret[key]=[True,""]
								else:
									ret[key]=[False,ret["msg"]]
								#ret[key]=self.core.get_plugin(key).restore(tmp_dir+"/"+value)

							else:
								ret[key]=[False,"Plugin not found"]
						except Exception as e:
							print(e)
							ret[key]=str(e)
							
					#Fix ipxeboot symlink restore
					ipxeLinkPath=("/var/www/ipxeboot")
					ipxeRealPath=os.path.realpath(ipxeLinkPath)
					try:
						if not(os.path.exists(ipxeRealPath)):
							print("Fixing ipxeboot symlink...")
							os.remove(ipxeLinkPath)
							os.symlink("/usr/share/llxbootmanager/www-boot",ipxeLinkPath)
					except Exception as e:
						print(e)
						ret[key]=str(e)
					
					self.final_operations()
					self.restoring_version=None
					return n4d.responses.build_successful_call_response(ret)
					
				except Exception as e:
					return n4d.responses.build_failed_call_response(RESTORE_ERROR,str(e))
					
			else:
				return n4d.responses.build_failed_call_response(RESTORE_FILE_NOT_FOUND_ERROR,"Backup file not found")
				return [False,{},"File not found"]
			
		else:
			return n4d.responses.build_failed_call_response(RESTORE_FILE_NOT_FOUND_ERROR,"Backup file not found")
			
	
		return n4d.responses.build_failed_call_response(RESTORE_UNKNOWN_ERROR,"Nothing was done")
		
		
	#def server_basics_restore
	
	
	def final_operations(self):
		

		try:
			self.core.get_plugin("Golem").startup(None)
			self.core.get_plugin("NetFoldersManager").startup(None)
						
			for item in self.core.get_plugin("Golem").light_get_user_list()["return"]:
				
				user_info={}
				user_info["profile"]=item[5]
				user_info["uid"]=item[1]
				user_info["uidNumber"]=item[2]
				try:
					objects["Golem"].exist_home_or_create(user_info)
				except:
					pass
						
			self.core.get_plugin("Golem").restore_groups_folders()
			self.core.get_plugin("ZeroServerWizardManager").end_operations()
			
			return n4d.responses.build_successful_call_response()
					
		except Exception as e:
				
			return n4d.responses.build_failed_call_response(FINAL_OPERATIONS_ERROR,str(e))

		
	#def final_operations

#class ServerBackupManager


if __name__=="__main__":
	
	golem=ServerBackupManager()
