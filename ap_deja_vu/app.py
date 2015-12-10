import glob
import json
import os

from flask import Flask, render_template, request
app = Flask(__name__)

DATA_DIR = os.environ.get('AP_DEJAVU_DATA_DIRECTORY', None)

@app.route('/favicon.ico')
def favicon():
    return ''

@app.route('/')
def index():
    context = {}
    context['elections'] = []
    if DATA_DIR:
        context['elections'] = [a.split('/')[-1] for a in glob.glob('%s*' % DATA_DIR)]
    return json.dumps(context)

@app.route("/<election_date>/status")
def status(election_date):
    """
    The route /<election_date>/status will return the status of a given
    election date test, including the current position in the hopper, the
    playback speed, and the path of the file that will be served at the current
    position.
    """
    election_key = 'AP_DEJAVU_%s' % election_date

    hopper = glob.glob('%s%s/*' % (DATA_DIR, election_date))

    position = int(os.environ.get(election_key + '_POSITION', '0'))
    playback = int(os.environ.get(election_key + '_PLAYBACK', '1'))

    return json.dumps({
                'playback': playback, 
                'position': position,
                'file': hopper[position]
            })

@app.route("/<election_date>")
def replay(election_date):
    """
    The route `/<election_date>` will replay the election files found in the folder
    `/<DATA_DIR>/<election_date>/`. The files should be named such that the first file
    will be sorted first in a list by `glob.glob()`, e.g., a higher letter (a) or lower
    number (0). Incrementing UNIX timestamps (such as those captured by Elex) would be
    ideal.

    This route takes two optional control parameters. Once these have been passed to set
    up an election test, the raw URL will obey the instructions below until the last
    file in the hopper has been reached.

    * `position` will return the file at this position in the hopper. So, for example,
    `position=0` would set the pointer to the the first file in the hopper and return it.
    
    * `playback` will increment the position by itself until it is reset. So, for example, 
    `playback=5` would skip to every fifth file in the hopper.

    When the last file in the hopper has been reached, it will be returned until the Flask
    app is restarted OR a new pair of control parameters are passed.

    Example: Let's say you would like to test an election at 10x speed. You have 109
    files in your `/<DATA_DIR>/<election_date>/` folder named 001.json through 109.json

    * Request 1: `/<election_date>?position=0&playback=10` > 001.json
    * Request 2: `/<election_date>` > 011.json
    * Request 3: `/<election_date>` > 021.json
    * Request 4: `/<election_date>` > 031.json
    * Request 5: `/<election_date>` > 041.json
    * Request 6: `/<election_date>` > 051.json
    * Request 7: `/<election_date>` > 061.json
    * Request 8: `/<election_date>` > 071.json
    * Request 9: `/<election_date>` > 081.json
    * Request 10: `/<election_date>` > 091.json
    * Request 11: `/<election_date>` > 101.json
    * Request 12: `/<election_date>` > 109.json
    * Request 13 - ???: `/<election_date>` > 109.json

    Requesting /<election_date>?position=0&playback=1 will reset to the default position
    and playback speeds, respectively.
    """
    election_key = 'AP_DEJAVU_%s' % election_date

    hopper = glob.glob('%s%s/*' % (DATA_DIR, election_date))

    position = int(os.environ.get(election_key + '_POSITION', '0'))
    playback = int(os.environ.get(election_key + '_PLAYBACK', '1'))

    if request.args.get('playback', None):
        try:
            playback = abs(int(request.args.get('playback', None)))
        except ValueError:
            return json.dumps({
                    'error': True,
                    'error_type': 'ValueError',
                    'message': 'playback must be an integer greater than 0.'
                })

    if request.args.get('position', None):
        try:
            position = abs(int(request.args.get('position', None)))
        except ValueError:
            return json.dumps({
                    'error': True,
                    'error_type': 'ValueError',
                    'message': 'position must be an integer greater than 0.'
                })

    os.environ[election_key + '_PLAYBACK'] = str(playback)

    if position + playback < len(hopper):
        os.environ[election_key + '_POSITION'] = str(position + playback)

    else:
        os.environ[election_key + '_POSITION'] = str(len(hopper))

    with open(hopper[position], 'r') as readfile:
        payload = str(readfile.read())

    return payload


if __name__ == "__main__":
    app.debug = True
    app.run()