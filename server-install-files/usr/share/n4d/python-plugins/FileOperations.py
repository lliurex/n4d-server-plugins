# -*- coding: utf-8 -*-

import base64

class FileOperations:

	def get_file_from_server(self,path):
		
		f=open(path,'rb')
		list=f.readlines()
		f.close()
		buf="".join(list)
		data=base64.b64encode(buf)
		return data
		
	#def get_file
	
	def send_file_to_server(self,buf64,server_file_name):
		
		buf=base64.b64decode(buf64)
		f=open(server_file_name,'wb')
		f.write(buf)
		f.close()
		
		return 1
		
	#def send_file_to_server
		

	
#class FileOperations