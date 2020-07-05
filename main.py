from os import path
import sys
import pyglet
from pyglet.window import key

#   BUILD:
#       pyinstaller main.py --noconsole --hidden-import='pkg_resources.py2_warn' -F --add-data ... --add-data ...
#       
#       or
#
#       pyinstaller main.spec
#

def resource_path(rp):
    bundle_dir = getattr(sys, '_MEIPASS', path.abspath(path.dirname(__file__)))
    return path.join(bundle_dir, rp)


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
    def __init__(self, operator):
        self.buffer = []
        self.required_operations = []


        self.executing = False
        self.dead = False

        self.state = 0

        self.operator = operator # the droid guides the operator

        self.accept_sound = pyglet.media.load(resource_path('droidsounds/droid_accept.wav'), streaming=False)
        self.wrong_sound = pyglet.media.load(resource_path('droidsounds/droid_wrong.wav'))

        self.button_sound = pyglet.media.load(resource_path('droidsounds/button.wav'), streaming=False)

        self.toggle = pyglet.media.load(resource_path('droidsounds/toggle.wav'), streaming=False) 


    def operate(self, op):
        if(not self.executing and not self.dead):

            self.button_sound.play()

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
    
    def execute_instructions(self, required_ops=None, required_pos=None, callback=None):
        if(not self.executing and not self.dead and (required_ops != None or required_pos != None)):
            self.toggle.play()
            self.required_operations = required_ops
            self.required_pos = required_pos
            print("BEGIN:")
            self.executing = True
            #TODO: play sound of "starting up" before executing
            pyglet.clock.schedule_interval(self.process_instructions, 0.4, callback=callback)
        elif self.dead:
            print("Droid is dead")
        elif self.executing:
            print("Executing... please wait")
        else:
            print("Unknown error executing")
            
        self.state = 0

    def process_instructions(self, *args, **kwargs):
        if self.buffer == []:
            pyglet.clock.unschedule(self.process_instructions)
            self.finish_operation(kwargs['callback'])
            print("END;")
        else:
            if len(self.buffer)>0:
                op = self.buffer.pop(0)
                print(op)
                #State machine
                if self.state == 1:
                    if op == key.F:
                        self.operator.move((-1, 0, 0))
                    elif op == key.T:
                        self.operator.move((0, 0, 1))
                    elif op == key.H:
                        self.operator.move((1, 0, 0))
                    elif op == key.B:
                        self.operator.move((0, 0, -1))

                if op == key.Y:
                    self.state = 1
                    self.operator.walking = True
                    self.operator.walking_player.play()

                if self.required_operations != None:
                    if len(self.required_operations) > 0 and op == self.required_operations.pop(0) and not self.dead:
                        print("accepted instruction")
                    else:
                        self.wrong_operation()
                elif self.required_pos != None and self.state==1 and not self.dead:
                    #play walking sound : CHECK
                    print("*walking*")
                

    def wrong_operation(self):
        self.dead = True        

    def failed_operation(self, callback=None):

        self.dead = True
        print("droid died")
        if callback:
            callback(False) #operation failed

    def accepted_operation(self, callback=None):
        self.accept_sound.play()

        print("accepted execution")
        if callback:
            callback(True) #operation complete

    def finish_operation(self, callback):
        self.executing = False
        if self.required_operations != None:
            if(len(self.required_operations)==0 and not self.dead):
                self.accepted_operation(callback)
            else:
                self.failed_operation(callback)
        elif self.required_pos != None:
            self.operator.walking = False
            self.operator.walking_player.pause()
            callback(self.required_pos)

class Operator:
    def __init__(self):
        self.listener = pyglet.media.get_audio_driver().get_listener()

        self.listener.position = (5, 0, 6)

        self.droid = Droid(self)
        self.control = Control()

        self.walking = False
        walking_sound = pyglet.media.load(resource_path('soundscape/walking.wav'), streaming=False) 
        self.walking_player = pyglet.media.Player()
        self.walking_player.queue(walking_sound)
        self.walking_player.loop = True
    
    def move(self, v):
        self.listener.position = Util.transform_position(v, self.listener.position)
        print(self.listener.position)

    def key_pressed(self, symbol, modifiers):
        if symbol in (key.V, key.B, key.N, key.F, key.G, key.H, key.R, key.T, key.Y, key.C):
            self.droid.operate(symbol)
        elif symbol == key.SPACE:
            #TODO: UNCOMMENT THIS ?
            # if self.control.is_transmitting():
            #     print("Is transmitting, please wait before moving")
            # else:
            if len(self.droid.buffer)>0:
                nop = self.control.get_next_operations()
                if isinstance(nop, tuple):
                    self.droid.execute_instructions(required_pos=nop, callback=self.droid_finished)
                elif isinstance(nop, list):
                    self.droid.execute_instructions(required_ops=nop, callback=self.droid_finished)
                    #todo: elif string -> its a voice command
            else:
                print("droid buffer empty. not requesting more information")


    def droid_finished(self, *args):
        if (self.droid.required_operations != None and args[0]) or (self.droid.required_pos != None and args[0] == self.listener.position):
            print("droid finished successfully")
            self.control.next_transmission()
        else:
            self.droid.wrong_sound.play()
            self.control.gameover()
            print("droid died during execution")



TOTAL_VOICE_TRANSMISSIONS = 9

class ControlTransmissions(pyglet.media.Player):
    def load_voice(self, voicen):
        return pyglet.media.load(resource_path('controlvoice/voice'+str(voicen)+'.wav'))

    def __init__(self):
        super().__init__()

        for i in range(TOTAL_VOICE_TRANSMISSIONS):
            self.queue(self.load_voice(i))

        self.play()

    def on_player_eos(self):
        # todo: add soundtrack play here
        print("game finished successfully!")

        w.close()
    
    def on_eos(self):

        #Todo: add soundtrack playing while paused
        self.pause()
    
    def next(self):
        self.next_source()
        self.play()

class Control:
    def __init__(self):
        self.transmissions = ControlTransmissions()

        self.operations = [
            [118, 104, 114, 116],
            (1, 0, 3),
            [102, 102, 110, 116],
            [114],
            # "Yes",
            # "Apple",
            (0, 0, 6),
            [103, 103, 103],
            (3, 0, 0),
            [98, 103, 114, 110, 116, 103, 104]
        ]

        #sequence to finish the game
        #   V H R T SPACE ... Y B B B F F F F SPACE ... F F N T SPACE ... R SPACE ... Y F T T T SPACE ... G G G SPACE ... Y H H H B B B B B B SPACE ... B G R N T G H SPACE ...


    def gameover(self):
        self.transmissions.pause()
        go = pyglet.media.load(resource_path('controlvoice/voice9.wav'))
        go.play()

    def get_next_operations(self):
        if len(self.operations)>0:
            return self.operations.pop(0)
        else:
            print("All control operations were transmitted.")
            return None

    def is_transmitting(self):
        return self.transmissions.playing
    
    def next_transmission(self):
        self.transmissions.next()


if __name__ == "__main__":
    w = GameWindow()
    pyglet.app.run()
