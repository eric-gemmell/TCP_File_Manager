import socket
import sys
import os
import base64
import time

def NewClientSocket(serverAddress, serverPort):
	"""
	Creates a new socket to a given address at a port number
	
	Parameters:
	-----------
	serverAddress: str
		The address of the server, either their IP address or text address
		some strings are formatted to mean localHost

	serverPort: int
		The port number to access

	Return:
	-------
	clientSocket: socket
		The socket oppened to then be used by a client when performing TCP requests
	
	Exceptions:
	-----------
	Connection refused: Connection to port failed, ensure Server is running and you know its address

	"""
	localHostAddresses = ["0.0.0.0","127.0.0.1","localhost",""," "]
	if(serverAddress in localHostAddresses):
		serverAddress = socket.gethostname()
	clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	clientSocket.connect((serverAddress,serverPort))
	print("\nConnected to Server: {} At Port: {}".format(serverAddress,serverPort))
	return clientSocket

def NewServerSocket(port):
	"""
	Creates a new socket at a given port number

	Parameters:
	-----------
	serverPort: int
		The port number to access

	Return:
	-------
	serverSocket: socket
		A socket listenning on a given port able to reseive TCP requests
	
	Exceptions:
	-----------
	Access Denied: attempting to access port that is either in use or requires sudo priveleges, use sudo if in doubt
	"""
	serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serverSocket.bind((socket.gethostname(), port))
	serverSocket.listen(5)
	print("New Server Listenning on Port: {}".format(port))
	return serverSocket

def SendValue(socket,markerString,value):
	"""
	Sends a variable to a given socket, converts the value to bytes, adds a string indicating the variable type for decompression
	And Surrounds it with a markerString to denote begining and end of values

	Parameters:
        -----------
        socket: socket
                The socket to which you will send the data

	value: str or list or int or bytes
		The variable to be sent

	markerString: str
		The string that will surround the value in order to denote its begining and end positions

        Return:
        -------
	
        Exceptions:
        -----------
        TypeError: Returned when user attempts to send a non accepted type.
	"""
	socket.sendall(markerString.encode())
	if(type(value) == bytes):
		socket.sendall("//BYTES//".encode())
		socket.sendall(value)
	elif(type(value) == str):
		socket.sendall("//STR//".encode())
		socket.sendall(value.encode())
	elif(type(value) == int):
		socket.sendall("//NUM//".encode())
		socket.sendall((str(value)).encode())
	elif(type(value) == list):
		for listElement in value:
			SendValue(socket,"//LIST//",listElement)
	else:
		raise TypeError("{} is not yet supported for sending.".format(type(value)))
	socket.sendall(markerString.encode())
	
def SendDictionary(socket,dictionaryToSend):
	"""
	Sends A Dictionary to a given socket, can send to either Server or Client Socket.
	Accepted format for variables within the dictionary are str, byte, int and list

	Parameters:
	-----------
	socket: socket
		The socket to which you will send the data

	dictionaryToSend: dict
		The dictionary that is sent to the socket

	Return:
	-------

	Exceptions:
	-----------
	TypeError: Returned when user attempts to send a non accepted type.
	"""
	if(type(dictionaryToSend) != dict):
		raise(TypeError("Value to send not a Dictionary"))
	for key, value in dictionaryToSend.items():
		SendValue(socket,"//KEY//",key)
		SendValue(socket,"//VALUE//",value)
	socket.sendall(("//END//").encode())

def DecodeValue(encodedValue):
	"""
	Converts b'//valueType//value//' To valueType(value.decode())
	Parameters:
	-----------
	encodedValue: bytearray
		the encoded value in binary containing a marker for its type

	Return:
	-------
	value: str, byte, int or list
		The Value extracted from and encoded back to its type from encodedValue

	Exceptions:
        -----------
        ValueError: "Incorrectly Formatted String"
                Returned when the message array has been formatted incorrectly
                Correct Format is: "//ValueType//your_value_here"...

	"""
	if(encodedValue.find("//BYTES//".encode()) == 0):
		return encodedValue[9:]
	elif(encodedValue.find("//STR//".encode()) == 0):
		return encodedValue[7:].decode()
	elif(encodedValue.find("//NUM//".encode()) == 0):
		return int(encodedValue[7:].decode())
	elif(encodedValue.find("//LIST//".encode()) == 0):
		extractedList = []
		while(len(encodedValue) > 0):
			listElement, encodedValue = ExtractValueFromData("//LIST//",encodedValue)
			extractedList.append(listElement)
		return extractedList
	raise ValueError("Incorrectly formatted String")

def ExtractValueFromData(markerString, inputData):
	'''	
	Converts '"markerString""typeMarker"Value"markerString"moreFromInputData'
	To '"typeMarker"Value' and 'moreFromInputData'

	Parameters:
	-----------
	markerString: str
		string that encapsulates the value wanted to extract

	inputData: bytearray
		the string that need to be parsed containing your value, corresponds to receivedData

	Return:
	--------
	key: str
		the value encapsulated between your marker

	inputData: str
		inputData substring with the removed analyzed chunk

	Exceptions:
	-----------
	ValueError: "Incorrectly Formatted String"
		Returned when the message array has been formatted incorrectly
		Correct Format is: "//KEY////KeyType//your_key_here//KEY////VALUE////valueType//your_value_here//VALUE//"...
	'''
	markerBytes = markerString.encode()
	markerStartPos = inputData.find(markerBytes)
	markerEndPos = inputData[markerStartPos+len(markerBytes):].find(markerBytes)
	if(markerStartPos != 0 or markerEndPos == -1):
		raise ValueError("Incorrectly Formatted String")
	encodedValue = inputData[markerStartPos+len(markerBytes):markerStartPos+len(markerBytes)+markerEndPos]
	value = DecodeValue(encodedValue)

	return value, inputData[markerStartPos+len(markerBytes)+markerEndPos+len(markerBytes):]

def ReceiveData(socket):
	"""
	Listens on a given socket and outputs a byte array corresponding to the sent array until the stop signal

	Parameters:
        -----------
        socket: socket 
                The socket on which to listen for a message

        Return:
        --------
	receivedData: bytearray
		The entire byte array received from the socket to be further processed into a dictionary

        Exceptions:
        -----------
        RuntimeError: "Timeout Exception"
                Too much time for an upload, exiting the process
	"""
	data = bytearray(1)
	receivedData = bytearray(0)
	startTime = time.time()
	timeSinceLastValue = time.time()
	while (len(data) > 0):
		if(startTime + 10 < time.time()):
			raise RuntimeError("Excessive upload duration")
		if(timeSinceLastValue + 3 < time.time()):
			raise RuntimeError("No exit string received, sender considered broken")
		data = socket.recv(4096)
		receivedData += data
		if(len(data) > 0):
			timeSinceLastValue = time.time()
		if(bytes("//END//","utf-8") in receivedData):
			receivedData = receivedData[:-7]
			break
	return receivedData

def ReceiveDictionary(socket):
	'''	
	Outputs a Dictionary from a given socket that has sent one
	
	Parameters:
	-----------
	socket: socket 
		The socket on which to listen for a message

	Return:
	--------
	Dictionary: dict
		A dictionary with all the key value pairs that were sent

	Exceptions:
	-----------
	RuntimeError: "Timeout Exception"
		Too much time for an upload, exiting the process

	ValueError: "Incorrectly Formatted String"
		Returned when the message array has been formatted incorrectly
		Correct Format is: "//KEY////STR//your_key_here//KEY////VALUE////ValueType//your_value_here//VALUE//"...
	'''
	receivedData = ReceiveData(socket)
	dictionary = {}
	while(len(receivedData) > 0):
		key,receivedData = ExtractValueFromData("//KEY//",receivedData)
		value,receivedData = ExtractValueFromData("//VALUE//",receivedData)
		dictionary[key] = value
	return dictionary

