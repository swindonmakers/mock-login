from datetime import datetime

def create_response(flag="success", code=200, info=None, data=None):
    """Create a standardized response dictionary"""
    response = {
        "request": {
            "date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z"),
            "status": {
                "flag": "success",
                "code": 200
            }
        },
        "result": {
            "status": {
                "flag": flag,
                "code": code
            }
        }
    }
    
    if info:
        response["result"]["status"]["info"] = info
    if data:
        response["result"]["data"] = data
    
    return response
