def custom_remote_dispatch_logic(self):
	
		try:
			servermode = int(llxvars["SRV_HOST_ID"])
		except:
			servermode = 0
			
		if servermode >0 and servermode <254:
			return True
		else:
			return False
			

	
	
#def logic

	

