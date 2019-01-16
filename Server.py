import socket
import sys
import SocketLibrary 
import os
import time
import datetime

ARTBABY = "\n██████╗ ███████╗ █████╗  ██████╗ ██████╗  ██████╗██╗  ██╗     ██████╗ ███████╗███╗   ███╗███╗   ███╗███████╗██╗     ██╗\n██╔══██╗██╔════╝██╔══██╗██╔════╝██╔═══██╗██╔════╝██║ ██╔╝    ██╔════╝ ██╔════╝████╗ ████║████╗ ████║██╔════╝██║     ██║\n██████╔╝█████╗  ███████║██║     ██║   ██║██║     █████╔╝     ██║  ███╗█████╗  ██╔████╔██║██╔████╔██║█████╗  ██║     ██║\n██╔═══╝ ██╔══╝  ██╔══██║██║     ██║   ██║██║     ██╔═██╗     ██║   ██║██╔══╝  ██║╚██╔╝██║██║╚██╔╝██║██╔══╝  ██║     ██║\n██║     ███████╗██║  ██║╚██████╗╚██████╔╝╚██████╗██║  ██╗    ╚██████╔╝███████╗██║ ╚═╝ ██║██║ ╚═╝ ██║███████╗███████╗███████╗\n╚═╝     ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝     ╚═════╝ ╚══════╝╚═╝     ╚═╝╚═╝     ╚═╝╚══════╝╚══════╝╚══════╝  (copyright)\n"
                                                                                                                            
def PrintStatus(responseDictionary,clientAddress, error = ""):
	print("[Time: {}]".format(datetime.datetime.fromtimestamp(time.time()).strftime('%H:%M:%S')))
	if(responseDictionary["status"] == 200):
		print ("Client at : {}, {}, status: {}, log: {}".format(clientAddress[0],clientAddress[1],responseDictionary["status"],responseDictionary["log"]))

	elif (responseDictionary["status"] == 400):
		print ("Client at : {}, {}, status {}, error: {}".format(clientAddress[0],clientAddress[1],responseDictionary["status"],responseDictionary["error"]))

	else:
		print("Internal Server Error for Client: {}, {}, error: {}".format(clientAddress[0],clientAddress[1],error))

def GetPort():
	"""
	Returns the port number to bind to, binds to 4000 as default if none is specified or if one is badly written
	"""
	port = 4000
	if(len(sys.argv) < 2):
		print ("No port specified, using 4000 as default")
	else:
		try:
			port = int(sys.argv[1])
		except:
			print ("Error, suplied port is not a number, using 4000")
		if(len(sys.argv) > 3):
			print ("Multiple arguments provided, using '{}' as port Number".format(port))
	
	return port

def GetResponseList(requestDictionary):
	"""
	Returns the responseDictionary for requests of type "List"
	
	Parameters:
	-----------
	requestDictionary: dict
		The Dictionary sent by the Client, requires nothing 

	Return:
	-------
	responseDictionary: dict
		The Dictionary to be sent as a response to the client, data is a list of elements in the dircetory
	
	Exceptions:
	-----------
	"""
	return {"status":200,"data":os.listdir(os.getcwd()),"command":"list","log":"List elements successful"}

def GetResponseGet(requestDictionary):
	"""
	Returns the responseDictionary for requests of type "Get", Either a 400 error if no file exists or 200 if successful
	responseDictionary contains a data parameter containing the data of the file
	
	Parameters:
	-----------
	requestDictionary: dict
		The Dictionary sent by the Client, requires a fileName parameter or will send a 400 response

	Return:
	-------
	responseDictionary: dict
		The Dictionary to be sent as a response to the client, can be an error
	
	Exceptions:
	-----------
	"""
	if "fileName" not in requestDictionary:
		return {"status":400,"error":"No fileName specified"}
	try:
		if(".." in requestDictionary["fileName"] or "/" in requestDictionary["fileName"]):
			return {"status":400,"error":"Unacceptable fileName, only localfiles allowed"}

		with open(requestDictionary["fileName"],"rb") as fileToSend:
			data = fileToSend.read()
			return {"status":200,"data":data,"fileName":requestDictionary["fileName"],"command":"get","log":"File Request '{}' Successful".format(requestDictionary["fileName"])}
	except Exception as e:
		return {"status":400,"error":"404 File Not Found"}

def GetResponsePut(requestDictionary):
	"""
	Returns the responseDictionary for requests of type "Put", Either a 400 error as file exists or no data provided, or 200 if successful
	
	Parameters:
	-----------
	requestDictionary: dict
		The Dictionary sent by the Client, requires a data and fileName parameter or will send a 400 response

	Return:
	-------
	responseDictionary: dict
		The Dictionary to be sent as a response to the client, can be an error
	
	Exceptions:
	-----------
	"""
	if ("fileName" not in requestDictionary) or ("data" not in requestDictionary):
		return {"status":400,"error":"Missing information for put command, missing data or fileName","log":str(requestDictionary)}
	if(".." in requestDictionary["fileName"] or "/" in requestDictionary["fileName"]):
		return {"status":400,"error":"Unacceptable fileName, only localfiles allowed"}
	if(requestDictionary["fileName"] in os.listdir(os.getcwd())):
		if("overrite" not in requestDictionary):
			return {"status":400,"error":"File {} already in directory, add '-f' to overrite".format(requestDictionary["fileName"])}
	f = open(requestDictionary["fileName"],"bw+")
	f.write(requestDictionary["data"])
	f.close()
	return {"status":200,"command":"put","log":"File Upload '{}' Successful".format(requestDictionary["fileName"])}

def GetResponse(requestDictionary):
	"""
	Returns a responseDictionary depending on the request received, This function calls a specific function for each type of request. A non recognized function will trigger a 400 response and an error.

	Parameters:
	-----------
	requestDictionary: dict
		The dictionary sent by the Client, should contain a key for: "command" with a value of either "get","put" or "list"

	Return:
	-------
	responseDictionary: dict
		The Dictionary to be sent as a response to the client, can be an error 

	Exceptions:
	-----------
	"""
	if "command" not in requestDictionary:
		return {"status":400,"error":"command not found in request"}
	knownCommands = {"list":GetResponseList,"get":GetResponseGet,"put":GetResponsePut}
	if(requestDictionary["command"] in knownCommands):
		return knownCommands[requestDictionary["command"]](requestDictionary)
	return {"status":400,"error":"command not recognized, recognized commands are: {}".format([key for key,value in knownCommands.items()])}

if (__name__ == '__main__'):
	"""
	Function Executed when script is executed. Creates a socket at given port and listens for requests,
	returns a dictionary depending on request type with certain parameters:
	"status":
		200, all okay, good request, good response
		400, request string of incorrect format, either file inaccessible, already exists, dictionary with wrong parameters
		500, internal server error
	"error":
		the type of error explained
	"log":
		A comprehensive log of the Servers processes
	"data":
		Optional when request is a get type, the data to be saved to a file

	Sever is made to always be listenning even if an error at some non fatal level is found
	"""
	print(ARTBABY)
	serverSocket = None
	try:
		serverSocket = SocketLibrary.NewServerSocket(GetPort())
	except:
		print ("Socket not accessible, check if already in use or check privileges")
		exit()
	while True:
		(clientSocket, clientAddress) = serverSocket.accept()		
		print ("\nNew Connection from {}".format(str(clientAddress)))
		requestDictionary = {}
		try:
			requestDictionary = SocketLibrary.ReceiveDictionary(clientSocket)
			if ("command"in requestDictionary):
				print("Received request: ",requestDictionary["command"])
		except Exception as e:
			PrintStatus({"status":400, "error":e},clientAddress) 
			SocketLibrary.SendDictionary(clientSocket,{"status":400,"error":str(e)})	
			continue
		try:
			responseDictionary = GetResponse(requestDictionary)
			PrintStatus(responseDictionary,clientAddress)
			SocketLibrary.SendDictionary(clientSocket,responseDictionary)
		except Exception as e:
			raise e
			try:
				SocketLibrary.SendDictionary(clientSocket,{"status":500,"error":"Internal server Error"})
			except Exception as e:
				PrintStatus({"status":500},clientAddress,str(e))
				continue
			PrintStatus({"status":500},clientAddress,str(e)) 
			continue


