from asyncio import current_task
import json
import sys
import tornado.gen
from tornado.ioloop import IOLoop
from wotpy.protocols.http.server import HTTPServer
from wotpy.wot.servient import Servient
import asyncio
from threading import Thread

CATALOGUE_PORT = 9300
HTTP_PORT = 9303

TD = {
    'title': 'Sensor-Detect',
    'id': 'it:unibo:filippo:benvenuti3:wot-detect',
    'description': '''A sensor which can detect presence of person.''',
    '@context': [
        'https://www.w3.org/2019/wot/td/v1',
    ],
    'properties': {
        'presence': {
            'type': 'string',
            'observable': True
        }
    },
    #'actions': { },
    'events': {
        'presenceChanged': {
            'description': '''Presence detection toggled.''',
            'data': {
                'type': 'string'
            },
        },
    },
}

def read_input():
    asyncio.set_event_loop(asyncio.new_event_loop())
    global exposed_thing
    while True:
        print("Enter 't' to turn the presence on, 'f' for off: ", end='')
        exposed_thing.properties['presence'].write("true" if input() == "t" else "false")

@tornado.gen.coroutine
def main():

    # Http service.
    http_server = HTTPServer(port=HTTP_PORT)
    
    # Servient.
    servient = Servient(catalogue_port=CATALOGUE_PORT)
    servient.add_server(http_server) # Adding http functionalities.

    # Start servient.
    wot = yield servient.start()

    global exposed_thing
    # Creating thing from TD.
    exposed_thing = wot.produce(json.dumps(TD))

    # Initialize thing property.
    exposed_thing.properties['presence'].write('true')

    # Observe presence value changing.
    exposed_thing.properties['presence'].subscribe(
        on_next=lambda data: exposed_thing.emit_event('presenceChanged', f'{data}'), # What to do when value change.
        on_completed= print('Subscribed for an observable property: presence'), # What to do when subscribed.
        on_error=lambda error: print(f'Error trying to observe presence: {error}') # What to do in case of error.
    )

    # Expose detection sensor thing.
    exposed_thing.expose()
    print(f'{TD["title"]} is ready')

    Thread(target=read_input).start()

if __name__ == '__main__':
    #asyncio.set_event_loop(asyncio.ProactorEventLoop())
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    IOLoop.current().add_callback(main)
    IOLoop.current().start()