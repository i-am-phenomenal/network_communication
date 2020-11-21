from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
from .decorators import Decorators

class Process(View): 
    decorators = Decorators()

    @decorators.validateRequestContentType
    @decorators.validateCommandContentType
    @decorators.validateCommandOperationTypes
    def post(self, request):
        return HttpResponse("Ok")

