class LessonManager:
	
	def get_lesson(self,lesson):
		
		try:
			print 1
			for plugin in cm.plugins:
				if plugin.class_name==lesson:
					if plugin.type=="python":
						f=open(plugin.path,"r")
						lines=f.readlines()
						f.close()
						ret=""
						for line in lines:
							ret+=line
						print 2
						plugin_info={}
						
						plugin_info["path"]=plugin.path
						plugin_info["type"]=plugin.type
						plugin_info["class_name"]=plugin.class_name
						plugin_info["function"]=plugin.function
						plugin_info["bin_name"]=plugin.bin_name
						plugin_info["args"]=plugin.args
						
						for x in plugin_info:
							if plugin_info[x]==None:
								plugin_info[x]=""
						

						
						return (plugin_info,ret)
					else:
						f=open(plugin.path,"r")
						lines=f.readlines()
						f.close()
						ret=""
						for line in lines:
							ret+=line
							
						plugin_info={}
						
						plugin_info["path"]=plugin.path
						plugin_info["type"]=plugin.type
						plugin_info["class_name"]=plugin.name
						plugin_info["function"]=plugin.function
						plugin_info["bin_name"]=plugin.bin_name
						plugin_info["args"]=plugin.args
						
						for x in plugin_info:
							if plugin_info[x]==None:
								plugin_info[x]=""
						
						
						
						return (plugin_info,ret)
			print 4
			return False
		except Exception as e:
			print e
			
		return False
		
	#def get_lesson

#class LessonManager