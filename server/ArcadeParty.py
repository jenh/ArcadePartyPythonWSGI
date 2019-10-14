import logging
import os, re
#import boto3
from werkzeug.contrib.cache import RedisCache

#dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

#table = dynamodb.Table('arcade_session')

from datetime import datetime

from flask import Flask, json, abort 
from flask_ask import Ask, question, statement, audio, current_stream, logger, session, request, convert_errors, context

application = Flask(__name__)
ask = Ask(application, "/",stream_cache=RedisCache(key_prefix="arcamb_",default_timeout=172800))
logging.getLogger('flask_ask').setLevel(logging.DEBUG)
FORMAT = '%(asctime)s - %(module)s - %(levelname)s - Thread_name: %(threadName)s - %(message)s'
logging.basicConfig(
    format=FORMAT, datefmt='%m/%d/%Y %I:%M:%S %p',
    filename='/tmp/arcade.log', level=logging.DEBUG)

year_cache = RedisCache(key_prefix="arcamb_year_",default_timeout=172800)

@ask.on_session_started
def start_session():
    logging.debug("Session started at {}".format(datetime.now().isoformat()))
    appid = str(session.application.applicationId)
    if appid != "amzn1.ask.skill.ce2004da-9cac-476d-b108-56733868eda6":
      abort(403)
    else:
        pass

@ask.launch
def handle_launch():
    return question("Welcome to Arcade Party. You can be transported to an arcade in 1981, 83, 86, or 92. Which do you choose?").reprompt("I'm sorry, I didn't get that. Say 1981, 1983, 1986, or 1992 to play Arcade Party")

@ask.intent('PlayIntent', default={'year': 'noidea'})
def handle_playintent(year):
    plainyear = str(year)
    sessionid = str(session.sessionId)
    userid = str(session.user.userId)
    year_cache.set(userid, plainyear)
    #if year is 'noidea':
    #    playurl = "https://archive.org/download/ArcadeAmbience/arcade86.mp3"
    #    speech = "Sorry, I didn't get that. I'm sure you want to feel like you're in an arcade, so I'll play sounds of 1986 for you!"
     #   return audio(speech).play(playurl) 
    if year is 'exit' or year is 'cancel' or year is 'exit' or year is 'stop' or year is 'quit':
        return statement("Shutting down your Arcade Party. Thanks for playing!")
    elif plainyear == "1981" or plainyear == "81":
        playurl = "https://archive.org/download/ArcadeAmbience/arcade.mp3"
        speech = "Now playing arcade sounds of nineteen eighty one" 
        return audio(speech).play(playurl)
    elif plainyear == "1983" or plainyear == "83": 
        playurl = "https://archive.org/download/ArcadeAmbience/arcade83.mp3"
        speech = "Now playing arcade sounds of nineteen eighty three" 
        return audio(speech).play(playurl)
    elif plainyear == "1986" or plainyear == "86":
        playurl = "https://archive.org/download/ArcadeAmbience/arcade86.mp3"
        speech = "Now playing arcade sounds of nineteen eighty six"
        return audio(speech).play(playurl)
    elif plainyear == "1992" or plainyear == "92":
        playurl = "https://archive.org/download/ArcadeAmbience/arcade92.mp3"
        speech = "Now playing arcade sounds of nineteen ninety two"
        return audio(speech).play(playurl)
    else:
        return question("Sorry, I  didn't quite get that. Would you like arcade ambiance from 1981, 1983, 1986, or 1992?")

@ask.intent('AMAZON.StopIntent')
def handle_stop():
    return audio("Thanks for playing!").stop()

@ask.intent('AMAZON.CancelIntent')
def handle_cancel():
    return audio("Thanks for playing!").stop()

@ask.intent('AMAZON.NextIntent')
def handle_next():
    userid = str(session.user.userId)
    my_year = year_cache.get(userid)
    my_year = re.sub('19','',my_year) 
    if my_year == "81":
        year = 83 
    elif my_year == "83":
        year = 86
    elif my_year == "86":
        year = 92
    elif my_year == "92":
        year = 81
    else:
        year = 92
    return handle_playintent(year)

@ask.intent('AMAZON.PreviousIntent')
def handle_back():
    userid = str(session.user.userId)
    my_year = year_cache.get(userid)
    my_year = re.sub('19','',my_year)
    if my_year == "81":
        year = 92
    elif my_year == "83":
        year = 81
    elif my_year == "86":
        year = 83
    elif my_year == "92":
        year = 86
    else:
        year = 83
    return handle_playintent(year)

@ask.intent('AMAZON.HelpIntent')
def handle_help():
    return question("Welcome to Arcade Party. Would you like to be audibly transported to an arcade in 1981, 1983, 1986, or 1992?")

@ask.intent('AMAZON.StartOverIntent')
def start_over():
    return handle_launch()

@ask.intent('AMAZON.PauseIntent')
def handle_pause():
    return audio("Stopping. Say Start to resume.").stop()

@ask.intent('AMAZON.ResumeIntent')
def handle_resume():
    return audio("Resuming playback.").resume()

@ask.session_ended
def session_ended():
    return "{}", 200


if __name__ == '__main__':
    if 'ASK_VERIFY_REQUESTS' in os.environ:
        verify = str(os.environ.get('ASK_VERIFY_REQUESTS', '')).lower()
        if verify == 'false':
            application.config['ASK_VERIFY_REQUESTS'] = False
    application.run(debug=True)

