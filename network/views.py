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

    def isDeviceNameValid(self, deviceName): 
        return len(deviceName) > 1

    def checkDeviceType(self, deviceType):
        return deviceType in ["COMPUTER", "REPEATER"]

    def performFetchCommand(self, command, commandText):
        if command == "devices": 
            pass
        
    def performCreateCommand(self, command, commandText):
        if command == "devices": 
            commandBody = commandText[2]
            commandBody = json.loads(commandBody)
            if self.isDeviceNameValid(commandBody["name"]) and self.checkDeviceType(commandBody["type"]):
                deviceObject = Device(
                    deviceName = commandBody["name"],
                    deviceType = commandBody["type"]
                )
                try: 
                    deviceObject.save()
                except IntegrityError:
                    return "error" 
                return "ok"
            else:
                return "error"

    @decorators.validateRequestContentType
    @decorators.validateCommandContentType
    @decorators.validateCommandOperationTypes
    def post(self, request):
        commandText = request.body.decode("utf-8").split("\n")
        commandType, command = self.parseCommands(commandText)
        if commandType == "CREATE": 
            if self.performCreateCommand(command, commandText) == "ok":
                return HttpResponse(
                    "Created Device Successfully",
                    status=200
                )
            else: 
                return HttpResponse(
                    "Error while trying to create device, Possible Reasons are 1.) Maybe Device Name or Device Type format is invalid or Maybe a device already exists",
                    status=500
                )
        elif commandType == "FETCH": 
            formattedRecords = self.performFetchCommand(command, commandText)
        
        return HttpResponse("Ok")

