import multiprocessing
import threading
import subprocess

class ClientDiscover:
	
	def __init__(self):

		pass
		
	#def init
	
	def ping(self,ip_range):
		
		self.ip_list=[]
		ip1,ip2=ip_range
		min=int(ip1.split(".")[len(ip1.split("."))-1])
		max=int(ip2.split(".")[len(ip2.split("."))-1])
		
		splitted_ip=ip1.split(".")
		
		ip=""
		for num in range(0,3):
			ip+=splitted_ip[num] +"."
			
		
		self.limit=max-min
		self.ips_being_checked=[]
		
		for i in range(min,max+1):
			self.ips_being_checked.append(ip+str(i))
			thread=threading.Thread(target=self.ping_thread,args=(ip+ str(i),))
			thread.start()
			#self.ping_thread(ip+"."+ str(i))
		
		return self.ip_list
		
	#def ping
	
	def ping_thread(self,ip):
		
		p=subprocess.Popen(["ping","-c","1",ip],stdout=subprocess.PIPE)
		output=p.communicate()[0]
		self.ips_being_checked.remove(ip)
		if output.find("Unreachable")==-1:
			self.ip_list.append(ip)
			#self.ip_list.sort()

		#self.limit-=1
		
		return True
	
	#def myping
	
	

#class ClientDiscover


if __name__=="__main__":
	t=ClientDiscover()
	list=t.ping(("10.0.0.129","10.0.0.254"))
	for item in list:
		from xmlrpclib import *
		try:
			server = ServerProxy ("https://" + item + ":9779")
			server.get_methods()
			print("[*] ======================================== [*]")
			print("[*] " + item + " seems to be a Lliurex system  [*]")
			try:
				ret=server.lliurex_version("","LliurexVersion")
				if type(ret)!=type(""):
					print("\t" + ret[1])
				print("[*] ======================================== [*]")
				print("")
			except:
				print("Maybe not... lliurex-version failed")
		except:
			pass
			#print "\t\t[!] " + item + " is not a Lliurex system [!]"

	