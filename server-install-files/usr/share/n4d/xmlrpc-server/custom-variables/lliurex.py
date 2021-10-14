def getLliurexVariables():
	
	try:
		
		p1=subprocess.Popen(["n4d-vars","listvars"],stdout=subprocess.PIPE)
		output=p1.communicate()[0]
		#output=output.replace("'","")
		tmp1=output.split(';\n')

		dic={}

		for item in tmp1:
			tmp2=item.split('=',1)
			tmp2=tmp[1:len(tmp)-1]
			if len(tmp2)>1:
				dic[tmp2[0]]=tmp2[1]


		return dic
	except:
		return {}

# getLliurexVariables


def strip_accents(s,remove_apostrophe=True):
	
	if type(s)!=type(unicode()):
		s=unicode(s,'utf-8')
		
	ret=''.join((c for c in unicodedata.normalize('NFKD', s) if unicodedata.category(c) != 'Mn'))
	if remove_apostrophe:
		ret=ret.replace("'","")
	return ret
		
		
def generate_uid(name,surname):
	
	name=strip_accents(name)
	surname=strip_accents(surname)
	
	name=name.encode("utf-8")
	surname=surname.encode("utf-8")
	
	name=name.lower()
	surname=surname.lower()
		
	name_list=name.split(" ")
	surname_list=surname.split(" ")
		
	uid=""
		
	for i in range(0,len(name_list[0])):
		uid=uid+name_list[0][i]
		if len(uid)==3:
			break
				
	last_surname=len(surname_list)-1
	if surname_list[last_surname]=="" and last_surname>0:
		last_surname-=1
		
	for i in range(0,len(surname_list[last_surname])):
		uid=uid+surname_list[last_surname][i]
		if len(uid)==6:
			break
			
	return uid
		
		
#def generateUid


def lliurex_version():
	try:
		output=[item.strip() for item in subprocess.Popen(["lliurex-version"],stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()[0].strip("\n").split(",")]
		return output
	except:
		return None

#def lliurex_version

llxversion=lliurex_version()

