from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
from .decorators import Decorators
import json 
from .models import Device
from django.db import IntegrityError
from django.forms.models import model_to_dict

def searchForDevice(connected, destinationNodeName, currentPath):
        if connected == []:
            resp = {
                "found": False,
                "path": []
            }
            return resp
        else: 
            if connected[0].deviceName == destinationNodeName: 
                return {
                    "found": True,
                    "path": currentPath.append(connected[0].deviceName)
                }
            else:
                searchForDevice(connected[1: len(connected)], destinationNodeName, currentPath.append(connected[0].deviceName))


class Process(View): 
    decorators = Decorators()

    def parseCommands(self, commandText):
        commandText = commandText[0].split(" /")
        commandType = commandText[0]
        command = commandText[1].replace("\r", "")
        return commandType, command

    def getDeviceNameFromCommandText(self, commandText): 
        commandText = commandText[2]
        commandText = json.loads(commandText)
        return commandText["name"]

    def isDeviceNameValid(self, deviceName): 
        return len(deviceName) > 1

    def checkDeviceType(self, deviceType):
        return deviceType in ["COMPUTER", "REPEATER"]

    def getAllDevicesInTheNetwork(self): 
        allDevices = list(Device.objects.all())
        formattedDevices = [
            {
                "type": device.deviceType,
                "name": device.deviceName
            }
            for device in allDevices
        ]
        return {
            "message": {
                "devices": formattedDevices
            },
            "status": 200
        }

    def returnResponseDict(self, message, statusCode):
        responseDict = dict()
        responseDict["message"] = message
        responseDict["status"] = statusCode
        return responseDict

    def getGraphRepresentation(self):
        allDevices = Device.objects.all()
        cleaned = {}
        for device in allDevices: 
            allConnected = list(device.connectedDevices.all().values_list('deviceName', flat=True))
            cleaned[device.deviceName] = allConnected
        return cleaned

    def findPath(self, graph, start, end, path=[]):
        path = path + [start]
        if start == end: 
            return path
        if not start in graph:
            return None
        for node in graph[start]:
            if node not in path: 
                newPath = self.findPath(graph, node, end, path)
                if newPath:
                    return newPath
        return None

    @decorators.checkIfFromAndToPresent
    @decorators.checkIfAllNodesPresentInDatabase
    @decorators.checkIfAnyNodeIsRepeater
    def getInfoRouteBetweenNodes(self, commandText):
        commandText = commandText[0].split(" /")[1].split("?")[1]
        sourceNode = commandText.split("&")[0].split("=")[1]
        destinationNode = commandText.split("&")[1].split("=")[1]
        source = self.getDeviceObjectByDeviceName(sourceNode)
        graph = self.getGraphRepresentation()
        path = self.findPath(graph, sourceNode, destinationNode)
        if path is None:
            return {
                    "message": json.dumps(
                        {"msg": "Route not found"}
                    ),
                    "status" : 404
            }
        else:
            return {
                "message": json.dumps(
                    {"msg": "Route is {route}".format(route="->".join(path))}
                ),
                "status" : 200
            }

    def performFetchCommand(self, command, commandText):
        if command == "devices": 
            return self.getAllDevicesInTheNetwork()

        elif "info-routes" in command: 
            return self.getInfoRouteBetweenNodes(commandText)
            

    def getDeviceObjectByDeviceName(self, sourceNode):
        deviceObject = Device.objects.get(
            deviceName =sourceNode.strip()
        )
        return deviceObject

    @decorators.checkIfConnectionsParamsValid
    @decorators.checkIfSourceNodeExists
    @decorators.checkIfSourceEqualsTargets
    @decorators.checkIfTargetNodesExist
    @decorators.checkIfDevicesAreAlreadyConnected
    def connectDevicesInTheNetwork(self, commandText): 
        commandBody = json.loads(commandText[2])
        if "source" in commandBody: 
            sourceNode = commandBody["source"]
            sourceObject = self.getDeviceObjectByDeviceName(sourceNode)
            targetNodes = commandBody["targets"]
            targetNodeObjs = Device.objects.filter(deviceName__in=targetNodes)
            sourceObject.connectedDevices.add(*targetNodeObjs)
            return self.returnResponseDict(
                "Successfully connected",
                200
            )
        

    def createDevice(self, commandText): 
        commandBody = commandText[2]
        commandBody = json.loads(commandBody)
        if self.isDeviceNameValid(commandBody["name"]): 
            if self.checkDeviceType(commandBody["type"]):
                deviceObject = Device(
                    deviceName = commandBody["name"],
                    deviceType = commandBody["type"]
                )
                try: 
                    deviceObject.save()
                    return self.returnResponseDict(
                        "Successfully added {deviceName}".format(deviceName=commandBody["name"]),
                        200
                    )
                except IntegrityError:
                    return self.returnResponseDict(
                       "Device {deviceName} already exists".format(deviceName =commandBody["name"]),
                        400
                    )
            else: 
                return self.returnResponseDict(
                       "type {deviceType} is not supported".format(deviceType =commandBody["type"]),
                        400
                )
        else:
             return self.returnResponseDict(
                "Invalid Device Name",
                400
            )

    def performCreateCommand(self, command, commandText):
        if command == "devices": 
            return self.createDevice(commandText)
            
        elif command == "connections": 
            return self.connectDevicesInTheNetwork(commandText)

    @decorators.validateRequestContentType
    @decorators.validateCommandContentType
    @decorators.validateCommandOperationTypes
    def post(self, request):
        commandText = request.body.decode("utf-8").split("\n")
        commandType, command = self.parseCommands(commandText)
        if commandType == "CREATE": 
            responseDict = self.performCreateCommand(command, commandText)
            return HttpResponse(
                json.dumps(
                    {"msg" : responseDict["message"]}
                ),
                status=responseDict["status"]
            )
        elif commandType == "FETCH": 
            response = self.performFetchCommand(command, commandText)
            if response["status"] == 400 or response["status"] == 404:
                return HttpResponse(
                    json.dumps(
                        {"msg": response["message"]}
                    ),
                    status=400
                )
            else:
                return HttpResponse(
                    json.dumps(response["message"]),
                    status=response["status"]
                )

    #Made for my own purposes
    def get(self, request):
        allDevices = Device.objects.all()
        formatted = []
        for device in allDevices: 
            allConnected = list(device.connectedDevices.all().values_list('deviceName', flat=True))
            cleaned = {
                "deviceName": device.deviceName,
                "connected": allConnected
            }
            formatted.append(cleaned)
        print(formatted)
        return HttpResponse(
            json.dumps(formatted),
            status=200
        )
