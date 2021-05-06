import subprocess
import os
import shutil
import os.path
import grp
import pwd
import pipes

import n4d.server.core

class NetFilesManager:
	
	CONF_FOLDER="/var/lib/lliurex-folders/"
	
	
	def __init__(self):

		self.core=n4d.server.core.Core.get_core()
		self.net_path = "/net/server-sync/"
		self.nethome_path = os.path.join(self.net_path ,"home")
		
		self.groups_path=self.net_path+"/groups_share/"		
		
		self.acls=[]
		self.acls.append("-m g:teachers:rwx")
		self.acls.append("-m g:admins:rwx")
		
		self.home_acls=[]
		self.home_acls.append("-m u:%s:rwx")
		
		self.check_main_folder()

	def startup(self,options):
		
		pass
		
		
	#def startup

	
	def create_home(self,user_info):
		group = user_info["profile"]
		if group == "admin":
			group = "admins"
		uid = user_info["uid"]
		nethome = os.path.join(self.nethome_path,group,uid)
		
		if not os.path.exists(nethome):
			userid = int(user_info["uidNumber"])
			nobody_id = int(pwd.getpwnam("nobody").pw_uid)
			usergid = int(grp.getgrnam("nogroup").gr_gid) 
			#fix umask for fix correct permission
			prevmask = os.umask(0)
			os.mkdir(nethome,0o2770)
			#shutils.copytree("/etc/skel/UserFiles",nethome,symlinks=True)
			#p1=subprocess.Popen(["rsync","-rltgD","/etc/skel-net/",pipes.quote(nethome)])
			command='rsync -rltgD /etc/skel-net/ "%s"'%nethome
			p1=os.system(command)
			
			#out = p1.communicate()
			
			'''
				#chown -R user:guser
				#chmod 770 for all directories
				#chmod 660 for all files
			'''
			os.lchown(nethome, nobody_id,usergid)
			for base ,directories, files in os.walk(nethome):
				for directori in directories:
					auxpath = os.path.join(base ,directori)
					os.lchown(auxpath,userid,usergid)
					os.chmod(auxpath,0o2770)
			
				for auxfile in files:
					auxpath = os.path.join(base,auxfile)
					os.chown(auxpath,userid,usergid)
					os.chmod(auxpath,0o660)	
			# for 

			# restore old umask
			os.chmod(nethome,0o2770)
			os.umask(prevmask)
			for acl in self.home_acls:
				#command='setfacl %s "%s"'%(acl%str(userid),pipes.quote(nethome))
				command='setfacl %s "%s"'%(acl%str(userid),nethome)
				os.system(command)
		return nethome
		
		
	#def createHome
	
	def delete_home(self,user_info):
		nethome = os.path.join(self.nethome_path,user_info["profile"],user_info["uid"])
		self.delete_directory(nethome)
		return nethome
	
	#def delete_home
	
	
	def delete_directory(self,directorypath):
		
		if os.path.exists(directorypath):
			try:
				shutil.rmtree(directorypath)
			except OSError:
				print("This path is a link")
			except :
				pass
		else:
			print("This path does not exist ")
	#def delete_directory
	
	def exist_home_or_create(self,user_info,mode=0):

		group = user_info["profile"]
		if group == "admin":
			group = "admins"
		uid = user_info["uid"]
		nethome = os.path.join(self.nethome_path,group,uid)

		if not os.path.exists(nethome):
			return self.create_home(user_info)
		else:
			if mode==0:
				#os.system("chown -R " + uid + ":nogroup '" + pipes.quote(nethome) + "'")
				command='chown -R "' + uid + '":nogroup "' + nethome + '"'
				os.system(command)
		return False

	#def exist_home_or_create
	
	
	def check_main_folder(self):
	
		if not os.path.exists(self.groups_path):
				
				try:
					os.mkdir(self.groups_path,0o775)
				except Exception as e:
					print(e)
					return -1
					
		return 0
	
	
	def create_group_folder(self,group_name):
		
		prevmask = os.umask(0)
		ok=True
		
		self.check_main_folder()
		
		if not os.path.exists(self.groups_path+group_name):
			
			try:
				os.mkdir(self.groups_path+group_name,0o750)
			except Exception as e:
				print(e)
				os.umask(prevmask)
				return -2

		else:
			os.chmod(self.groups_path+group_name,0o750)

		try:

			gid=grp.getgrnam(group_name).gr_gid
			os.chown(self.groups_path+group_name,0,int(gid))
			#command="setfacl %s '%s'"%(" ".join(self.acls),pipes.quote(self.groups_path+group_name))
			command='setfacl %s "%s"'%(" ".join(self.acls),self.groups_path+group_name)
			os.system(command)
			
		except Exception as e:
			print(e)
			os.umask(prevmask)
			return -3

		os.umask(prevmask)
		return 0
		
	#def create_group_folder
	
	def remove_group_folder(self,group_name):
		
		try:
			shutil.rmtree(self.groups_path+group_name)
		except Exception as e:
			print(e)
			
		return True
	
	
	
if __name__=="__main__":
	n=NetFilesManager(1)
