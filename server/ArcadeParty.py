import logging
import os, re
from werkzeug.contrib.cache import RedisCache

from datetime import datetime

from flask import Flask, json, abort 
from flask_ask import Ask, question, statement, audio, current_stream, logger, session, request, convert_errors, context

# Set up our Flask application
application = Flask(__name__)

# Connect to Redis, create the default key prefix. We set the timeout to 172800 seconds, which is 48 hours. You can change as needed.
ask = Ask(application, "/",stream_cache=RedisCache(key_prefix="arcparty_",default_timeout=172800))

# Configure logging. We're logging to /tmp/arcade.log; you can change this and the logging format to whatever you like.
logging.getLogger('flask_ask').setLevel(logging.DEBUG)
FORMAT = '%(asctime)s - %(module)s - %(levelname)s - Thread_name: %(threadName)s - %(message)s'
logging.basicConfig(
    format=FORMAT, datefmt='%m/%d/%Y %I:%M:%S %p',
    filename='/tmp/arcade.log', level=logging.DEBUG)

# Set up a key to store the last year played. Key times out after 48 hours
year_cache = RedisCache(key_prefix="arcparty",default_timeout=172800)

# This is what we do when an Alexa session initiates, we start logging and reject any connection that doesn't send the proper appid (change your_app_id to your Alexa app id:
@ask.on_session_started
def start_session():
    logging.debug("Session started at {}".format(datetime.now().isoformat()))
    appid = str(session.application.applicationId)
    if appid != "your_app_id":
      abort(403)
    else:
        pass

# This is what we do at launch, prompt the user to give us a year to play
@ask.launch
def handle_launch():
    return question("Welcome to Arcade Party. You can be transported to an arcade in 1981, 83, 86, or 92. Which do you choose?").reprompt("I'm sorry, I didn't get that. Say 1981, 1983, 1986, or 1992 to play Arcade Party")

# This is the meat of our skill, given a year, we play a corresponding audio file. We set up a session, save the session info to cache and play the correct audio file (or cancel/exit/quit/stop if somehow they ended up being sent to the PlayIntent). 

@ask.intent('PlayIntent', default={'year': 'noidea'})
def handle_playintent(year):
    plainyear = str(year)
    sessionid = str(session.sessionId)
    userid = str(session.user.userId)
    year_cache.set(userid, plainyear)
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

# When Alexa sends us a stop command, here's what we do:
@ask.intent('AMAZON.StopIntent')
def handle_stop():
    return audio("Thanks for playing!").stop()

# When Alexa sends us a cancel command, here's what we do:
@ask.intent('AMAZON.CancelIntent')
def handle_cancel():
    return audio("Thanks for playing!").stop()

# When Alexa sends us a next command, we figure out where we are, then jump to the next track by invoking the PlayIntent with the next year:
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

# If Alexa sends us a previous intent, we find the current track and play the last track by invoking the PlayIntent with the previous year.
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

# Basic help response:
@ask.intent('AMAZON.HelpIntent')
def handle_help():
    return question("Welcome to Arcade Party. Would you like to be audibly transported to an arcade in 1981, 1983, 1986, or 1992?")

# Relaunch:
@ask.intent('AMAZON.StartOverIntent')
def start_over():
    return handle_launch()

# Pause:
@ask.intent('AMAZON.PauseIntent')
def handle_pause():
    return audio("Stopping. Say Start to resume.").stop()

# Resume:
@ask.intent('AMAZON.ResumeIntent')
def handle_resume():
    return audio("Resuming playback.").resume()

# End the session, return 200:
@ask.session_ended
def session_ended():
    return "{}", 200

# Our main routine, :
if __name__ == '__main__':
    if 'ASK_VERIFY_REQUESTS' in os.environ:
        verify = str(os.environ.get('ASK_VERIFY_REQUESTS', '')).lower()
        if verify == 'false':
            application.config['ASK_VERIFY_REQUESTS'] = False
    application.run(debug=True)

