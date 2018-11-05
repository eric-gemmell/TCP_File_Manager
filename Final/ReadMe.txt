██████╗ ███████╗ █████╗  ██████╗ ██████╗  ██████╗██╗  ██╗     ██████╗ ███████╗███╗   ███╗███╗   ███╗███████╗██╗     ██╗     
██╔══██╗██╔════╝██╔══██╗██╔════╝██╔═══██╗██╔════╝██║ ██╔╝    ██╔════╝ ██╔════╝████╗ ████║████╗ ████║██╔════╝██║     ██║     
██████╔╝█████╗  ███████║██║     ██║   ██║██║     █████╔╝     ██║  ███╗█████╗  ██╔████╔██║██╔████╔██║█████╗  ██║     ██║     
██╔═══╝ ██╔══╝  ██╔══██║██║     ██║   ██║██║     ██╔═██╗     ██║   ██║██╔══╝  ██║╚██╔╝██║██║╚██╔╝██║██╔══╝  ██║     ██║     
██║     ███████╗██║  ██║╚██████╗╚██████╔╝╚██████╗██║  ██╗    ╚██████╔╝███████╗██║ ╚═╝ ██║██║ ╚═╝ ██║███████╗███████╗███████╗
╚═╝     ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝     ╚═════╝ ╚══════╝╚═╝     ╚═╝╚═╝     ╚═╝╚══════╝╚══════╝╚══════╝ 


Peacock Gemmell SocketLibrary.py is a simple socket library that in combination with Server.py and Client.py allows a user to send and receive files remotely to the location where Server.py or Client.py is running. Files are Non Encrypted. 

CODE EXECUTION:
---------------

In order to run either script, the SocketLibrary script must be placed in the same folder as each client and server script

Server startup:
---------------
	python3 Server.py <port number>

If no port is specified, 4000 is assumed as default
Port addresses bellow 1024 can be accessed under sudo privileges

example:
	python3 Server.py 3000
	python3 Server.py 
	sudo python3 Server.py 100

Client execution:
-----------------
	python3 Client.py <server address> <server port> <command> <parameter> <optional force "-f">

<server address> refers to the ip address of the server or its URL, for localHost access "" can be passed as default

<server port> is the port on which the server is running, set to 4000 as default on the server side, this parameter is obligatory

<command> command to be sent by the Client and executed by the server. Recognized commands are "list", "get" and "put", non recognized commands will be rejected by both Client and Server.
	list --> prints out line by line files and directories in the Server directory

	get --> returns a given file from the Servers directory, saved if file does not already exist, overwrite by adding -f

	put --> Saves a file from Clients directory to the servers directory, if it does not exist, overwrite by adding -f

<parameter> file names required for put and get commands (ex: ReadMe.txt)

example:
	python3 Client.py "" 3000 list
	python3 Client.py localHost 4000 get ReadMe.txt -f
	python3 Client.py 35.176.127.63 4000 put RandomFile.blend 

APPLICATION FUNCTION:
---------------------

Send/Receive Dictionary:
------------------------
At the heart of Sending and receiving TCP messages are SendDictionary and ReceiveDictionary within SocketLibrary.
These allow the Client and Server to flexibly and reliably send specific variables with an associated key to one another. 
Being able to send many or few variables of different types is very powerful and allows great flexibility, sending each value with an associated key allows the server not to require much processing of data, making developpement much more flexible.
Allowed variable types are str, int and bytes as well as lists of these.

When sending a dictionary, Key Value pairs are one by one checked for correct type and successively converted into byte arrays, then sent along with a tag indicating their original variable type.
They are surrounded by a marker, either "//VALUE//", "//KEY//" or other delimiting the beginning and end of the variable, making it easy for the receiver to recognize the variable limits. 
example for sending a key value pair: key1,value1:

b"//KEY////STR//key//KEY////VALUE////<valueType//value//VALUE////END//"

//END// is the end of message string, causing the Server to start decoding the message

Any deviation from this format will cause a FormatError within the receiver, exiting from the listenning process. It is evident that currently sending strings containing //END// or //VALUE// or //KEY// will cause a Format Error. This is not a security flaw however.

At the Receiving end, this bytearray is received in 4096 byte chunks, an arbitrary length as all received chunks are combined one after another.
The receivedData is processed after receiving the stop signal b"//END//", if the message takes longer that 10 seconds, the whole message is discarded
Key Value pairs are processed one after another by finding their start and end markerString (b"//KEY//", b"//VALUE//"), then reconverting the byte array to their type.
receivedData is thus each run cleaved of a key value pair, becoming shorter each run, until a length of 0 is acheived.
Cases where the final length of receivedData is non zero, or if a markerString is not directly located at the beginning of receivedData will cause errors
ex:
b"RandomGarble//KEY////STR//key//KEY////VALUE////<valueType//value//VALUE////END//
b"//KEY//randomGarble//STR//key//KEY////VALUE////<valueType//value//VALUE////END//
b"//KEY////STR//key//KEY//randomGarble//VALUE////<valueType//value//VALUE////END//

These will all cause formatting errors.

Therefore at the end of all this the receiving end gets exactly the same dictionary that was sent.

High Level Dessign:
-------------------

Client forms a requestDictionary containing command type, possibly data and/or a fileName to the Server.
The Server in response sends a responseDictionary, this time containing a status, an error or log string depending on the success or failure of the request.
The Client then prints out this response and the Server waits for another request.

Client:
-------
The program function overall is very simple, the client first gathers essential information from user input through the command line, as to what command to execute.
Depending on command type client will form a requestDictionary containing command type, and if necessary any additional data and fileName. If the command is not recognized an error is thrown.
If the file to be sent does not exist an error will obviously be thrown as it could not be read, and sent.
No check is made whether user is trying to access a file in another directory than that of the server, or if the file exists.
example requestDictionary:
	{"command":"list"}
	{"command":"get","fileName":"ReadMe.txt","override":"true"}
	{"command":"put","fileName":"ReadMe.txt","data":"42 is the meanning of life","override":"true"}

Server:
-------
The Server is constantly waiting for a request, upon receiving a dictionary, it will try to execute the requested command, if the message cannot be turned into a dictionary ie incorrectly formatted message, the requestDictionary is missinginformation, the command is not recognized, or a external file is trying to be accessed, the server will return a 400 status, indicating the client has sent a incorrect message. A error message is also sent allong with it.
If all works out, a 200 status response is sent, with a log message, and possibly some data.
Internal Server Errors are only natural, causing a 500 status response.

REASONS FOR DICTIONARY DESIGN:
-------------------------------
Dictionaries are really very flexible, and confortable when sending very different messages, with different types and amounts of data. 
In the beggining, we thought about sending a request message on the command type, to then receive a acnolige response, then followed by the sending of data followed by a final response. 
We both wondered how we could design this four message system to become flexible, as lists only required 2 messages, whereas puts and gets required 4. 
We wanted to have a systematic way of sending a request and getting a response that was the same for all 3 commands. Obviously our 4 message system was too complicated, which we realized, and decided to first think of a way of sending useful amounts of data across.
Dictionaries, for us were the perfect solution, as having a key value makes it easy to specify the intent of the value sent, they also allow variable amounts of data to be sent. and by allowing different types of variables to be sent, coding on top of the Send/Receive Dictionary method of SocketLibrary is really enjoyable and easy.
Difficulties consist in encoding values into binary, as they need to then be decoded back.
In addition, our initial version coded in python2.7 (#bestPython) treated strings and bytearray as same types, making it easy to send messages initially but upon transition to python3 it became a drag. Adding the variable type marker is a simple way of making decoding easy, sure it consumes bandwidth, but it makes life better.

With Dictionary sending available and on our 3rd version of Client and Server, we realized that sending 4 messages was absurdly complex for no reason, when you could just send 2, a request and a response.
It also made coding it much easier, no more 1st response then 2nd request then 2nd response.


Future Improvements:
--------------------
Things that are evident errors:
	if your file contains any markerStrings in it, such as "//END//" you will get a formatting error. This could be easily solved by finding these, adding a !in them, then removing it in decoding, but life is short.
	Encryption, files are sent directly through TCP unencrypted, not too important, until in a previous version I accidentaly sent my server pem file over TCP as the server could access any parent and child directory.
		Maybe RSA public private key could be fun.
	Your file cannot contain ".." or "/" as these are normally associated with changing sirectory, and we can't have that.




