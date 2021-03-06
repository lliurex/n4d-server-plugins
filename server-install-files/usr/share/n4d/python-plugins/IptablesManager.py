import os
import subprocess

import n4d.server.core

class IptablesManager:
	
	def __init__(self):
		
		os.system("modprobe ipt_owner")
		
		self.iptables_tc_skel="iptables -%s OUTPUT -o %s -m owner --uid-owner %s -m comment --comment N4D_IPTABLES_TC -j DROP"
		self.iptables_fc_skel="iptables -%s FORWARD -s %s  -p tcp ! -d 10.0.0.0/8 -m comment --comment N4D_IPTABLES_FC -j DROP"
		self.blocked_list={}
		
		self.core=n4d.server.core.Core.get_core()
		
	#def init
	
	
	def block(self,user,ip):
		
		self.get_iptables_list()

		if ip=="127.0.0.1":
			#thin
			if user not in self.blocked_list:
			
				#eth=objects["VariablesManager"].get_variable("EXTERNAL_INTERFACE")
				ret=self.core.get_variable("EXTERNAL_INTERFACE")
				if ret["status"]!=0:
					return 1
				eth=ret["return"]
				cmd=self.iptables_tc_skel%("I",eth,user)
				os.system(cmd)
			
			return n4d.responses.build_successful_call_response(0)
			
		#fat

		if ip not in self.blocked_list:
			cmd=self.iptables_fc_skel%("I",ip)
			os.system(cmd)
		
		return n4d.responses.build_successful_call_response(1)
		
		
	#def block_user
	
	def unblock(self,user,ip):
		
		self.get_iptables_list()
		
		if ip=="127.0.0.1":
			#thin
			if user in self.blocked_list:
			
				ret=self.core.get_variable("EXTERNAL_INTERFACE")
				if ret["status"]!=0:
					return 1
				eth=ret["return"]
				cmd=self.iptables_tc_skel%("D",eth,user)
				os.system(cmd)
				
			return n4d.responses.build_successful_call_response(0)
		
		#fat
		if ip in self.blocked_list:
		
			cmd=self.iptables_fc_skel%("D",ip)
			os.system(cmd)

		return n4d.responses.build_successful_call_response(1)
		
	#def unblock_user
	
	def is_blocked(self,item):
		
		ret=False
		
		if item in self.blocked_list:
			ret=True
			
		return n4d.responses.build_successful_call_response(ret)
		
	#def is_user_blocked
	
	
	def blocked_list(self):
		
		self.get_iptables_list()
		return n4d.responses.build_successful_call_response(self.blocked_list())
		
	#def blocked_list
	
	def get_iptables_list(self):
		
		self.blocked_list={}
		
		output=subprocess.Popen(["iptables -L | grep N4D"],stdout=subprocess.PIPE,shell=True).communicate()[0].decode("utf-8")
		for line in output.split("\n"):
			if len(line)>1:
				line=line.split(" ")
				#0 7 9 11 24 37:
				target,prot,opt,source,destination,comment=line[0],line[7],line[9],line[11],line[24]," ".join(line[37:])
				try:
					user,client_type=line[40],line[42]
					ip="127.0.0.1"
				except:
					user=source
					ip=source
					client_type="N4D_IPTABLES_FC"
					
				
				info={}
				info["target"]=target
				info["prot"]=prot
				info["opt"]=opt
				info["source"]=source
				info["destination"]=destination
				info["comment"]=comment
				info["user"]=user
				info["client_type"]=client_type
				info["ip"]=ip
				self.blocked_list[user]=info
				

	#def iptables_list
	

#class IptablesManager


if __name__=="__main__":
	
	im=IptablesManager()
	im.get_iptables_list()
	for item in im.blocked_list:
		print("[%s]"%item)
		for item2 in im.blocked_list[item]:
			print("\t[%s] = %s "%(item2,im.blocked_list[item][item2]))
		
		
		
		
		