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

    def checkIfFromAndToPresent(self, function): 
        def innerFunction(*args, **kwargs): 
            params = args[1][0].split(" /")[1]
            if "from" in params and "to" in params:
                return function(*args, **kwargs)
            else: 
                return {
                    "message": "Invalid Request",
                    "status" : 400
                }
        return innerFunction

    def checkIfAllNodesPresentInDatabase(self, function):
        def innerFunction(*args, **kwargs):
            params = args[1][0].split(" /")[1]
            params = params.split("?")[1].split("&")
            sourceNode = params[0].split("=")[1]
            destinationNode = params[1].split("=")[1]
            if Device.objects.filter(deviceName=sourceNode).exists():
                if Device.objects.filter(deviceName=destinationNode).exists():
                    return function(*args, **kwargs)
                else: 
                    return {
                        "message": "Node {nodeName} not found".format(nodeName=destinationNode),
                        "status" : 400
                    }    
            else:
                return {
                    "message": "Node {nodeName} not found".format(nodeName=sourceNode),
                    "status" : 400
                }
        return innerFunction

    def checkIfAnyNodeIsRepeater(self, function): 
        def innerFunction(*args, **kwargs):
            params = args[1][0].split(" /")[1]
            params = params.split("?")[1].split("&")
            sourceNode = params[0].split("=")[1]
            destinationNode = params[1].split("=")[1]
            deviceTypes = list(Device.objects.filter(deviceName__in=[sourceNode, destinationNode]).values_list("deviceType", flat=True))
            if "REPEATER" in deviceTypes:
                return {
                    "message": "Route cannot be calculated with repeater",
                    "status" : 400
                }
            else: 
                return function(*args, **kwargs)
        return innerFunction


    def validateValueType(self, function):
        def innerFunction(*args, **kwargs):
            value = args[2]
            if type(value["value"]) == int:
                return function(*args, **kwargs)
            else: 
                return {
                    "message": "value should be an integer",
                    "status" : 400
                }
        return innerFunction

    def checkIfDeviceIsPresent(self, function):
        def innerFunction(*args, **kwargs):
            deviceName =args[1]
            if Device.objects.filter(deviceName=deviceName).exists():
                return function(*args, **kwargs)
            else: 
                return {
                    "message": "Device Not Found",
                    "status": 400
                }
        return innerFunction