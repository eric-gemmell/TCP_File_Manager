import sys
import SocketLibrary
import os

def GetServerAddress():
	"""
	Returns port number and serverAdress from user input

	Parameters:
	-----------
	
	Return:
	-------
	serverAddress: str
		the server which will be accessed's address 

	serverPort: int
		the server which will be accessed's port number

	Exceptions:
	-----------
	TypeException: Port Number is not a Number

	"""
	try:
		return sys.argv[1],int(sys.argv[2])
	except:
		print("Port Number {} is not a Number!".format(sys.argv[2]))
		exit()

def GetCommand():
	"""
	Returns a immature version of requestDictionary containing the command type
	Parameters:
	-----------
	
	Return:
	-------
	requestDictionary: dic
		The Dictionary that will be sent to the Server, at the moment it only contains the command type

	Exceptions:
	-----------
	ValueException: Non Recognized Command

	"""
	if(len(sys.argv) < 4):
		print ("Error, insufficient essential parameters. Please execute code in format python Client.py 'serverAddress' 'serverPort' 'command' optional'parameter'")
		exit()
	knownCommands = ["list","get","put"]
	if(sys.argv[3] not in knownCommands):
		print ("Error, Unkown command, '{}'  allowed commands: {}".format(sys.argv[3],knownCommands))
		exit()
	return {"command":sys.argv[3]}	

def GetParametersList():
	"""
	Returns the parameters to be added to the requestDictionary in case of command "list"
	Parameters:
	-----------
	
	Return:
	-------
	requestDictionary: dic
		the parameters to be sent to the Server	

	Exceptions:
	-----------
	"""
	return {}
def GetParametersGet():
	"""
	Returns the parameters to be added to the requestDictionary in case of command "get"
	Parameters:
	-----------
	
	Return:
	-------
	requestDictionary: dic
		the parameters to be sent to the Server	

	Exceptions:
	-----------
	ArgumentError: No file To download indicated
	"""
	if(len(sys.argv) < 5):
		print ("Error, Parameter 'File to Download' Missing.")
		exit()
	if(len(sys.argv) == 6):
		if(sys.argv[5] == "-f"):
			return {"fileName":sys.argv[4],"overrite":"True"}
	return {"fileName":sys.argv[4]}

def GetParametersPut():
	"""
	Returns the parameters to be added to the requestDictionary in case of command "put"
	Parameters:
	-----------
	
	Return:
	-------
	requestDictionary: dic
		the parameters to be sent to the Server, the data of the file, filename and whether to override or not

	Exceptions:
	-----------
	ArgumentError: No file To upload indicated

	FileError: Unable to read file, check whether exists or permissions
	"""
	if(len(sys.argv) < 5):
		print ("Error, Parameter 'File to Upload' Missing.")
		exit()
	data = ""
	try:
		with open(sys.argv[4],"rb") as fileToUpload:
			data = fileToUpload.read()
		if(len(sys.argv) == 6):
			if(sys.argv[5] == "-f"):
				return {"data":data,"fileName":sys.argv[4],"overrite":"True"}
		return {"data":data,"fileName":sys.argv[4]}
	except Exception as e:
		print (e)
		exit()	

def CreateRequestDictionary():
	"""
	Returns the requestDictionary to be sent to the Server

	Parameters:
	-----------

	Return:
	-------
	requestDictionary: dic
		the parameters to be sent to the Server, command with parameters depending on command type

	Exceptions:
	-----------
	ArgumentError: No file To upload indicated

	FileError: Unable to read file, check whether exists or permissions

	ValueException: Non Recognized Command
	
	ArgumentError: No file To download indicated
	"""
	requestDictionary = GetCommand()
	getParameterFunctions = {"list":GetParametersList,"get":GetParametersGet,"put":GetParametersPut}
	requestDictionary.update(getParameterFunctions[requestDictionary["command"]]())
	return requestDictionary

if(__name__ == "__main__"):
	"""
	Generates a requestDictionary depending on user input, commands can either be "list","get" or "put"
	Then waits for a responseDictionary from the server, if no response is received returns an error
	prints the response depending on command type
	"""
	requestDictionary = CreateRequestDictionary()
	clientSocket = None
	try:
		ServerAddress,ServerPort = GetServerAddress()
		clientSocket = SocketLibrary.NewClientSocket(ServerAddress,ServerPort)
	except:
		print("Connection to {} at port {} Failed, ensure Server is running and you know its address".format(ServerAddress,ServerPort))
		exit()
	SocketLibrary.SendDictionary(clientSocket,requestDictionary)
	responseDictionary = {}
	try:
		responseDictionary = SocketLibrary.ReceiveDictionary(clientSocket)
		print("Response received")
	except (ValueError,RuntimeError) as e:
		print (e)
		exit()
	if("status" in responseDictionary):
		print("\nstatus: {}".format(responseDictionary["status"]))
		if(responseDictionary["status"] != 200):
			print("Error Message: {}\n".format(responseDictionary["error"]))
		else:
			print("Log Message: {}\n".format(responseDictionary["log"]))
			if(requestDictionary["command"] == "get"):
				try:
					if("overrite" not in requestDictionary): 
						with open(requestDictionary["fileName"],"bx") as downloadedFile:
							downloadedFile.write(responseDictionary["data"])
							print("File {} saved Succesfully!".format(requestDictionary["fileName"]))
					else:
						with open(requestDictionary["fileName"],"bw") as downloadedFile:
							downloadedFile.write(responseDictionary["data"])
							print("File {} saved Succesfully!".format(requestDictionary["fileName"]))
				except Exception as e:
					print (e)
					print("File {} was Unable to save add -f to force".format(requestDictionary["fileName"]))
			elif(requestDictionary["command"] == "list"):
				for fileName in responseDictionary["data"]:
					print(fileName)
	else:
		print("Incorrectly Formatted response")
