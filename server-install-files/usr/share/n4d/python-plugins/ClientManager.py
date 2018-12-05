import time
import threading


class Client:
	
	def __init__(self,user,ip):
		
		if ":" in ip:
			self.ip=ip.split(":")[0]
			self.thin_client=True
		else:
			self.ip=ip
			self.thin_client=False
			
		self.user=user
		self.last_sol=time.mktime(time.localtime()) # last SignOfLife time.localtime(self.last_sol)
		
	#def init
	
	
#class Client

CLIENT_MANAGER_SLEEP_TIME=200

class ClientManager:
	
	def __init__(self):
		
		self.clients=[]
		
		t=threading.Thread(target=self.check_client_list)
		t.setDaemon(True)
		t.start()
		
	#def __init__
	
	def register_client(self,user_dic):
		
		for user in user_dic:
			
			client=Client(user,user_dic[user])
			found=False	
			found_list=[]
			for item in self.clients:
				if client.user==item.user:
					found=True
					found_list.append(item)
			if found:
				ip_found=False
				for item in found_list:
					if client.ip==item.ip:
						item.last_sol=client.last_sol
						ip_found=True
						break
				if not ip_found:
					self.clients.append(client)
			else:
				self.clients.append(client)
				
		return True
		
	#def register_client
	
	def get_client_list(self):
		return self.clients
	#def get_client_list
		
	def check_client_list(self):
		while True:
			
			checking_time=time.mktime(time.localtime())
			print ""
			print "[ClientManager] Checking client list... [" + str(checking_time) + "]"
			
			for client in self.clients:
				print "\t* " + client.user + ", from ip: " + client.ip
				if client.last_sol + CLIENT_MANAGER_SLEEP_TIME < checking_time:
					print "\t\t[!] Last sign of life expired. Removing from list..."
					print "\t\t" + str(client.last_sol+CLIENT_MANAGER_SLEEP_TIME) + " < " + str(checking_time)
					self.clients.remove(client)
					
					if client.user in objects["TeacherShareManager"].get_paths():
						print "\t\tRemoving shared folder from TeacherShareManager service..."
						objects["TeacherShareManager"].remove_path(client.user)
					
				
					
			
			time.sleep(CLIENT_MANAGER_SLEEP_TIME)
			
	#def check_client_list
	
	
	
#class ClientManager

if __name__=="__main__":
	cm=ClientManager()
	while True:
		pass