import pyglet
from pyglet.window import key

#   BUILD:
#       pyinstaller main.py --noconsole --hidden-import='pkg_resources.py2_warn' -F
#

# Fixes for building
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# label = pyglet.text.Label('Hello, world',
#                           font_name='Times New Roman',
#                           font_size=36,
#                           x=window.width//2, y=window.height//2,
#                           anchor_x='center', anchor_y='center')


# gmq = pyglet.media.Player() #global media queue

# gmq.queue(sosmc)

class GameWindow(pyglet.window.Window):
    def __init__(self, **kwargs):
        kwargs.update(dict(
            width=1280,
            height=720,
            caption='Operator',
            resizable=True,
        ))
        super(GameWindow, self).__init__(**kwargs)
        # self.set_fullscreen(True)

        self.operator = Operator()

        self.soundsources = []

        warsounds = pyglet.media.Player()
        warsounds.queue(pyglet.media.load(resource_path('soundscape/warsounds.wav')))
        warsounds.loop = True
        # warsounds.volume = 0.7
        self.soundsources.append(warsounds)

        # x.position = Util.transform_position((5,5,0), x.position)

        self.sources_group = pyglet.media.PlayerGroup(self.soundsources)
        self.sources_group.play()

    def on_draw(self):
        self.clear()

    def on_key_press(self, symbol, modifiers):
        self.operator.key_pressed(symbol, modifiers)

class Util:
    def transform_position(v, l):
        return (l[0] + v[0], l[1] + v[1], l[2] + v[2])

class Droid:
    def __init__(self):
        self.buffer = []
        self.required_operations = []
        self.executing = False

        self.dead = False

    def operate(self, op, ):
        if(not self.executing and not self.dead):
            if op == key.C:
                self.buffer = []
            else:
                self.buffer.append(op)
            print(self.buffer)
        elif self.dead:
            print("Droid is dead")
        elif self.executing:
            print("Executing... please wait")
        else:
            print("Unknown error operating")
    
    def execute_instructions(self, required_ops=None, callback=None):
        if(not self.executing and len(self.buffer)>0 and not self.dead):
            self.required_operations = required_ops
            print("BEGIN:")
            self.executing = True
            #TODO: play sound of "starting up" before executing
            pyglet.clock.schedule_interval(self.process_instructions, 0.5, callback=callback)
        elif len(self.buffer)==0:
            print("No operations to process")
        elif self.dead:
            print("Droid is dead")
        elif self.executing:
            print("Executing... please wait")
        else:
            print("Unknown error executing")
            

    def process_instructions(self, *args, **kwargs):
        if self.buffer == []:
            pyglet.clock.unschedule(self.process_instructions)
            self.finish_operation(kwargs['callback'])
            print("END;")
        else:
            op = self.buffer.pop(0)
            print(op)
            if len(self.required_operations) > 0 and op == self.required_operations.pop(0):
                print("accepted op")
            else:
                self.wrong_operation()
            
    def wrong_operation(self):
        #TODO: play wrong operation sound
        self.dead = True

    def failed_operation(self, callback=None):
        #TODO: droid blows up and the game ends - must play sound of explosion and message from control
        self.dead = True
        print("droid died")
        if callback:
            callback(False) #operation failed

    def accepted_operation(self, callback=None):
        print("accepted execution")
        if callback:
            callback(True) #operation complete

    def finish_operation(self, callback):
        self.executing = False
        if(len(self.required_operations)==0):
            self.accepted_operation(callback)
        else:
            self.failed_operation(callback)

class Operator:
    def __init__(self):
        self.listener = pyglet.media.get_audio_driver().get_listener()

        self.droid = Droid()
        self.control = Control()
    
    def move(self, v):
        self.listener.position = Util.transform_position(v, self.listener.position)
        print(self.listener.position)

    def key_pressed(self, symbol, modifiers):
        if symbol in (key.V, key.B, key.N, key.F, key.G, key.H, key.R, key.T, key.Y, key.C):
            self.droid.operate(symbol)
            #TODO: UNCOMMENT THIS FOR FINALS
        elif symbol == key.SPACE:
            if self.control.is_transmitting() and symbol == key.SPACE:
                print("Is transmitting, please wait before moving")
            else:
                self.droid.execute_instructions(self.control.get_next_operations(), self.droid_finished)
        elif symbol == key.A:
            self.move((-1, 0, 0))
        elif symbol == key.W:
            self.move((0, 0, 1))
        elif symbol == key.D:
            self.move((1, 0, 0))
        elif symbol == key.S:
            self.move((0, 0, -1))

    def droid_finished(self, *args):
        if args[0]:
            print("droid finished successfully")
            self.control.next_transmission()
        else:
            print("droid died during execution")


TOTAL_VOICE_TRANSMISSIONS = 2

class ControlTransmissions(pyglet.media.Player):
    def load_voice(self, voicen):
        return pyglet.media.load('controlvoice/voice'+str(voicen)+'.wav')
    def __init__(self):
        super().__init__()

        for i in range(TOTAL_VOICE_TRANSMISSIONS):
            self.queue(self.load_voice(i))

        #TODO: Play "interrupt with transmission sound"
        self.play()
    
    def on_eos(self):
        self.pause()
    
    def next(self):
        #TODO: Play "interrupt with transmission sound"
        self.next_source()
        self.play()

class Control:
    def __init__(self):
        self.transmissions = ControlTransmissions()

    def get_next_operations(self):
        return [118, 104, 114, 116]

    def is_transmitting(self):
        return self.transmissions.playing
    
    def next_transmission(self):
        self.transmissions.next()

if __name__ == "__main__":
    w = GameWindow()
    pyglet.app.run()