import lliurex.net

class IpManager:
	
	#objects is a n4d-core variable
	
	def get_server_ip(self):
		
		return lliurex.net.get_ip(objects["VariablesManager"].get_variable("SRV_NIC"))
		
	#def get_server_ip
	
	def get_server_broadcast(self):
		
		return lliurex.net.get_broadcast(objects["VariablesManager"].get_variable("SRV_NIC"))
		
	#def get_server_broadcast
	
	def get_server_bitmask(self):
		
		return lliurex.net.get_bitmask(objects["VariablesManager"].get_variable("SRV_NIC"))
		
	#def get_server_bitmask
	
	def get_server_netmask(self):
		
		return lliurex.net.get_netmask(objects["VariablesManager"].get_variable("SRV_NIC"))
		
	#def get_server_netmask


#class IpManager