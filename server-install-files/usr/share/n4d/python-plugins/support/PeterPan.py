import os
import subprocess
import threading

class PeterPan:

	def __init__(self,attributes=None):
		self.attributes = attributes
		self.thread_list=[]
		
		
	#def init
	
	def execute_python_dir(self,dir,NEVERLAND_VAR=None,ARGV=None):
		
		t=threading.Thread(target=self.execute_python_dir_thread,args=(dir,NEVERLAND_VAR,ARGV))
		t.daemon=True
		#t.start()
		
		self.thread_list.append(t)
		
		if len(self.thread_list)==1:
			self.wake_master_thread()
		
		return True
		
	#def execute_dir
	
	def execute_binary_dir(self,dir,NEVERLAND_VAR=""):
		
		t=threading.Thread(target=self.execute_binary_dir_thread,args=(dir,NEVERLAND_VAR))
		t.daemon=True
		#t.start()
		
		self.thread_list.append(t)
		
		if len(self.thread_list)==1:
			self.wake_master_thread()
		
		return True
		
	#def execute_binary_dir
	
	
	def wake_master_thread(self):
		
		t=threading.Thread(target=self.execute_workers)
		t.daemon=True
		t.start()
		
	#def wake_master_thread
	
	
	def execute_workers(self):
		
		while len(self.thread_list)>0:
			
			self.thread_list[0].start()
			self.thread_list[0].join()
			self.thread_list.pop(0)
			
		#END OF MAIN THREAD
			
	#def execute_workers
	
	
	
	def execute_python_dir_thread(self,dir,NEVERLAND_VAR=None,ARGV=None):
		'''
		In this case NEVERLAND_VAR can be a list
		'''
		if os.path.exists(dir):
			
			list=os.listdir(dir)
			list.sort()
			for item in list:
				if os.path.isfile(dir+"/"+item):
					try:
						execfile(dir+"/"+item,locals())
					except:
						pass		
		
	#def execute_python_dir_thread
	
	def execute_binary_dir_thread(self,dir,NEVERLAND_VAR=""):
		
		list=os.listdir(dir)
		list.sort()
		for item in list:
			subprocess.Popen([dir+"/"+item,NEVERLAND_VAR],stdout=subprocess.PIPE)
			
	#def execute_binary_dir_t
	
	
	
#class PeterPan

if __name__=="__main__":

	pp=PeterPan()
	pp.execute_binary_dir("/home/hector/test")
