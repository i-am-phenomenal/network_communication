from .exceptions import CustomException
from django.http import HttpResponse
import json
from .models import Device

class Decorators():

    def __init__(self): 
        self.possibleOperationTypes = [
            "CREATE",
            "MODIFY",
            "FETCH"
        ]

    def validateRequestContentType(self, function):
        def innerFunction(*args, **kwargs): 
            contentType = args[1].content_type
            if contentType == "text/plain":
                return function(*args, **kwargs)
            else: 
                return HttpResponse("Error", status=500)
        return innerFunction
        
    def validateCommandContentType(self, function): 
        def innerFunction(*args, **kwargs): 
            body = args[1].body.decode("utf-8").split("\n")
            body = [ele for ele in body if ele]
            if body[0].split(" /")[0] == "FETCH":
                return function(*args, **kwargs)
            if len(body) <= 1: 
                return HttpResponse(
                    json.dumps(
                        {"msg": "Invalid Command."}
                    ),
                    status=400
                )
            commandContentType = body[1].split(" : ")[1]
            commandContentType = commandContentType.replace("\r", "")
            if commandContentType == "application/json": 
                return function(*args, **kwargs)
            else: 
                return HttpResponse("Error", status=500)
        return innerFunction
            

    def validateCommandOperationTypes(self, function): 
        def innerFunction(*args, **kwargs):
            command = args[1].body.decode("utf-8").split("\n")
            command = [ele for ele in command if ele]
            if command[0].split(" /")[0] == "FETCH":
                return function(*args, *kwargs)
            if len(command) <= 1: 
                return HttpResponse(
                    json.dumps(
                        {"msg": "Invalid Command."}
                    ),
                    status=400
                )
            operationType = args[1].body.decode("utf-8").split("\n")[0].split(" /")[0]
            if operationType in self.possibleOperationTypes:
                return function(*args, *kwargs)
            else: 
                return HttpResponse("Error", status=500)
        return innerFunction


    def checkIfConnectionsParamsValid(self, function): 
        def innerFunction(*args, **kwargs):
            params = json.loads(args[1][2])
            if "source" in params and "targets" in params:
                return function(*args, **kwargs)
            else: 
                return {
                    "message": "Invalid command syntax",
                    "status" : 400
                }
        return innerFunction

    def checkIfSourceNodeExists(self, function):
        def innerFunction(*args, **kwargs):
            params = json.loads(args[1][2])
            sourceNode = params["source"].strip()
            if Device.objects.filter(deviceName=sourceNode).exists():
                return function(*args, **kwargs)
            else:
                return {
                    "message": "Node '{nodeName}' not found".format(nodeName=sourceNode),
                    "status" : 400
                }
        return innerFunction

    def checkIfSourceEqualsTargets(self, function):
        def innerFunction(*args, **kwargs):
            params = json.loads(args[1][2])
            sourceNode = params["source"].strip()
            targetNodes = params["targets"]
            for target in targetNodes: 
                if target.strip() == sourceNode:
                    return {
                    "message": "Cannot connect device to itself",
                    "status" : 400
                }
                else:
                    pass
            return function(*args, **kwargs)
        return innerFunction

    def checkIfDevicesAreAlreadyConnected(self, function):
        def innerFunction(*args, **kwargs):
            params = json.loads(args[1][2])
            sourceNode = params["source"].strip()
            targetNodes = params["targets"]
            sourceObj = Device.objects.get(deviceName=sourceNode)
            allConnectedDevices  = sourceObj.connectedDevices.all()
            for device in allConnectedDevices: 
                if device.deviceName in targetNodes: 
                    return {
                        "message": "Devices are already connected",
                        "status": 400
                    }
                else:
                    pass
            return function(*args, **kwargs)
        return innerFunction

    def checkIfTargetNodesExist(self, function):
        def innerFunction(*args, **kwargs):
            params = json.loads(args[1][2])
            targetNodes = params["targets"]
            for node in targetNodes:
                if not Device.objects.filter(deviceName=node).exists():
                    return {
                        "message": "Node '{nodeName}' not found".format(nodeName=node),
                        "status" : 400
                    }
                else:
                    pass
            return function(*args, **kwargs)
        return innerFunction