"""
This is a Python template for Alexa to get you building skills (conversations) quickly.
"""

from __future__ import print_function
# from botocore.vendored import requests
import requests
import json

import dateutil.tz

import datetime



# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple'
            # 'title': "SessionSpeechlet - " + title,
            # 'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }

def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def convert_pred(isotime):
    '''
    Takes in a time in iso format for a prediction
    Return the seconds left for that prediction
    '''
    eastern = dateutil.tz.gettz('US/Eastern')
    current = datetime.datetime.now(tz=eastern).replace(tzinfo=None)
    arrival = datetime.datetime.strptime(isotime[:-6], "%Y-%m-%dT%H:%M:%S")
    delta = arrival - current
    seconds=delta.seconds
    return seconds


def get_mit_prediction(stop_number=13,pred=False):
    '''
    Returns current MIT Beacon Street @ Mass Ave(stop_number=13) shuttle predictions from MIT API
    http://m.mit.edu/apis/shuttles/
    
    '''
    #generally "boston" for daytime
    r=requests.get("http://m.mit.edu/apis/shuttles/predictions/?agency=mit&stop_number={}".format(str(stop_number)))
    data=r.json()

    routes=[rt for rt in data if rt["predictable"] if "boston" in rt["route_id"]] #check for my target route
    if routes==[]:
        if pred:
            return []
        else:
            return "There are no predictions at this time"

    route=routes[0] #grab a route
    route_name=route["route_title"] #get the title
    stop_name=route["stop_title"]
    predictions=[round(prediction["seconds"]/60,1) for prediction in route["predictions"]]
    prediction_str=""
    if len(predictions)==1:
        prediction_str=str(predictions[0])
        output="The next {} shuttle is coming in {} minutes to {}".format(route_name,prediction_str,stop_name)
    else:
        #return output
        #only get two predictions
        predictions.sort()
        prediction_str="{} and {}".format(predictions[0],predictions[1])
        output="The next {} shuttles are coming in {} minutes to {}".format(route_name,prediction_str,stop_name)
    if pred:
        return predictions
    else:
        return output


def get_OneBus_prediction(stop_number=95,pred=False):

    r=requests.get("https://api-v3.mbta.com//predictions?filter[stop]={}".format(str(stop_number)))
    
    data=r.json()

    # routes=[rt for rt in data["data"] if rt["attributes"]["status"]=="null"] #check for my target route
    vehicles=data["data"]
    if vehicles==[]:
        if pred:
            return []
        else:
            return "There are no One Bus predictions at this time"

    route=vehicles[0] #grab a route
    route_name="One Bus to Harvard" #get the title
    stop_name="Beacon street at Mass ave"
    predictions=[round(convert_pred(vehicle["attributes"]["arrival_time"])/60,1) for vehicle in vehicles]
    prediction_str=""
    if len(predictions)==1:
        prediction_str=str(predictions[0])
        output="The next {} is coming in {} minutes to Beacon street at Mass ave".format(route_name,prediction_str)
    else:
        #return output
        #only get two predictions
        predictions.sort()
        prediction_str="{} and {}".format(predictions[0],predictions[1])
        output="The next {} are coming in {} minutes to {}".format(route_name,prediction_str,stop_name)

    if pred:
        return predictions
    else:
        return output

def get_harvard_prediction(stop_number=4068606,pred=False):
    
    "788d779028msh52a8f9ac864d914p1f8cacjsne6f39dc4a7f3"

    r = requests.get("https://transloc-api-1-2.p.mashape.com/arrival-estimates.json?agencies=64",
      headers={
        "X-Mashape-Key": "788d779028msh52a8f9ac864d914p1f8cacjsne6f39dc4a7f3",
        "Accept": "application/json"
      }
    )
    
    data=r.json()
    vehicles=[vehicle for vehicle in data["data"] if int(vehicle["stop_id"])==stop_number]
    
    if vehicles==[]:
        if pred:
            return []
        else:
            return "There are no Harvard Shuttle predictions at this time"

    route=vehicles[0] #grab a route
    route_name="M Two Shuttle to Harvard" #get the title
    stop_name="Beacon street at Mass ave"
    predictions=[round(convert_pred(vehicle["arrivals"][0]["arrival_at"])/60,1) for vehicle in vehicles]
    prediction_str=""
    if len(predictions)==1:
        prediction_str=str(predictions[0])
        output="The next {} is coming in {} minutes to Beacon street at Mass ave".format(route_name,prediction_str)
    else:
        #return output
        #only get two predictions
        predictions.sort()
        prediction_str="{} and {}".format(predictions[0],predictions[1])
        output="The next {} are coming in {} minutes to {}".format(route_name,prediction_str,stop_name)
    
    if pred:
        return predictions
    else:
        return output

def get_closest_predictions():
    '''
    Returns the two most close predictions
    Can be from MIT, Harvard or the OneBus
    '''
    # MIT  [9.5, 36.9, 66.9, 96.9]
    # 1bus  [5.4, 20.6, 33.4, 45.6, 56.8]
    best1,best2=(float("inf"),None),(float("inf"),None)
    mit=[(p,"MIT Shuttle") for p in get_mit_prediction(pred=True)]
    onebus=[(p,"One Bus") for p in get_OneBus_prediction(pred=True)]
    harvard=[(p,"Harvard Shuttle") for p in get_harvard_prediction(pred=True)]

    for pred in mit+onebus+harvard:
        pred2=pred
        if pred[0]<best1[0]:
            pred2=best1
            best1=pred
        if pred2[0]<best2[0] and pred2!=best1:
            best2=pred2

    predictions=[pred for pred in [best1,best2] if pred[1] is not None]

    if len(predictions)==0:
        return "There are no predictions at this time"
    if len(predictions)==1:
        route1=predictions[0][1]
        prediction1=str(predictions[0][0])
        output="The next shuttle coming into Beacon street is the {} in {} minutes".format(route1,prediction1)
    else:
        #return output
        #only get two predictions
        route1=predictions[0][1]
        prediction1=str(predictions[0][0])
        route2=predictions[1][1]
        prediction2=str(predictions[1][0])
        output="The next shuttles coming into Beacon street are the {} in {} minutes and the {} in {} minutes".format(route1,prediction1,route2,prediction2)
    return output


def get_boston_predictions():
    '''
    Returns the two most close predictions to Boston
    Can be from MIT, Harvard or the OneBus
    '''
    # MIT  [9.5, 36.9, 66.9, 96.9]
    # 1bus  [5.4, 20.6, 33.4, 45.6, 56.8]
    best1,best2=(float("inf"),None),(float("inf"),None)
    
    mit=[(p,"MIT Shuttle") for p in get_mit_prediction(stop_number=3, pred=True)]
    onebus=[(p,"One Bus") for p in get_OneBus_prediction(stop_number=75, pred=True)]
    harvard=[(p,"M Two Shuttle") for p in get_harvard_prediction(stop_number=4221960, pred=True)]
    stop_name="84 Mass Ave"

    for pred in mit+onebus+harvard:
        pred2=pred
        if pred[0]<best1[0]:
            pred2=best1
            best1=pred
        if pred2[0]<best2[0] and pred2!=best1:
            best2=pred2

    predictions=[pred for pred in [best1,best2] if pred[1] is not None]

    if len(predictions)==0:
        return "There are no predictions at this time"
    if len(predictions)==1:
        route1=predictions[0][1]
        prediction1=str(predictions[0][0])
        output="The next shuttle coming into {} is the {} in {} minutes".format(stop_name, route1,prediction1)
    else:
        #return output
        #only get two predictions
        route1=predictions[0][1]
        prediction1=str(predictions[0][0])
        route2=predictions[1][1]
        prediction2=str(predictions[1][0])
        output="The next shuttles coming into {} are the {} in {} minutes and the {} in {} minutes".format(stop_name, route1,prediction1,route2,prediction2)
    return output

def get_mit_prediction_response():
    """ An example of a custom intent. Same structure as welcome message, just make sure to add this intent
    in your alexa skill in order for it to work.
    """
    session_attributes = {}
    card_title = "MitShuttle"
    speech_output = get_mit_prediction()
    reprompt_text = "You look greater now"
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_OneBus_prediction_response():
    """ An example of a custom intent. Same structure as welcome message, just make sure to add this intent
    in your alexa skill in order for it to work.
    """
    session_attributes = {}
    card_title = "OneBus"
    speech_output = get_OneBus_prediction()
    reprompt_text = "You look greater now"
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_harvard_prediction_response():
    """ An example of a custom intent. Same structure as welcome message, just make sure to add this intent
    in your alexa skill in order for it to work.
    """
    session_attributes = {}
    card_title = "HarvardShuttle"
    speech_output = get_harvard_prediction()
    reprompt_text = "You look greater now"
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_closest_prediction_response():
    """ An example of a custom intent. Same structure as welcome message, just make sure to add this intent
    in your alexa skill in order for it to work.
    """
    session_attributes = {}
    card_title = "Closest"
    speech_output = get_closest_predictions()
    reprompt_text = "You look greater now"
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def get_boston_prediction_response():
    """ An example of a custom intent. Same structure as welcome message, just make sure to add this intent
    in your alexa skill in order for it to work.
    """
    session_attributes = {}
    card_title = "Boston"
    speech_output = get_boston_predictions()
    reprompt_text = "You look greater now"
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    session_attributes = {}
    card_title = "Welcome"
    
    speech_output = "What shuttle would you like to know the prediction for?"
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "I didn't catch that, can you repeat the shuttle again?"
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for trying the Alexa Skills Kit sample. " \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts.
        One possible use of this function is to initialize specific 
        variables from a previous state stored in an external database
    """
    # Add additional code here as needed
    pass

    

def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """
    # Dispatch to your skill's launch message
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "MitShuttle":
        return get_mit_prediction_response()
    elif intent_name == "OneBus":
        return get_OneBus_prediction_response()
    elif intent_name == "HarvardShuttle":
        return get_harvard_prediction_response()
    elif intent_name == "Closest":
        return get_closest_prediction_response()
    elif intent_name == "Boston":
        return get_boston_prediction_response()
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        return get_closest_predictions()


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.
    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("Incoming request...")

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])

