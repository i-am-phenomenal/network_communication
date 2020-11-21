from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
from .decorators import Decorators
import json 
from .models import Device
from django.db import IntegrityError

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
            "devices": formattedDevices
        }

    def returnResponseDict(self, message, statusCode):
        responseDict = dict()
        responseDict["message"] = message
        responseDict["status"] = statusCode
        return responseDict

    def performFetchCommand(self, command, commandText):
        if command == "devices": 
            return self.getAllDevicesInTheNetwork()

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
            formattedRecords = self.performFetchCommand(command, commandText)
            return HttpResponse(
                json.dumps(formattedRecords),
                status=200
            )
        
        return HttpResponse("Ok")

