from .exceptions import CustomException

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
                raise CustomException("Content Type is Invalid ")
        return innerFunction
        
    def validateCommandContentType(self, function): 
        def innerFunction(*args, **kwargs): 
            body = args[1].body.decode("utf-8").split("\n")
            commandContentType = body[1].split(" : ")[1]
            commandContentType = commandContentType.replace("\r", "")
            if commandContentType == "application/json": 
                return function(*args, **kwargs)
            else: 
                raise CustomException("Content Type is Invalid ")
        return innerFunction
            

    def validateCommandOperationTypes(self, function): 
        def innerFunction(*args, **kwargs):
            operationType = args[1].body.decode("utf-8").split("\n")[0].split(" /")[0]
            if operationType in self.possibleOperationTypes:
                return function(*args, *kwargs)
            else: 
                raise CustomException("Operation Type is invalid")
        return innerFunction