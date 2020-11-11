import gi, queue, can, threading, time
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

class GUIupdater():
    def __init__(self, builder):
        self.builder = builder

    def masterUpdate():
        pass

    def canUpdate(self, msg):
        t0 = time.time()
        buf = self.builder.get_object("input2").get_buffer()
        msg = self.shortMessage(self.recBuffer.get())
        #packet = self.buffer.get() #txt.set_text(msg)
        #txt = "ID:{}|DATA:{}".format(hex(packet.arbitration_id), str(packet.data))
        t = time.time() - t0
        buf.set_text(msg)

class CANListener(can.Listener):
    """
    Listener child class for calling GLib async GUI refresh with new can data.
    Notifier class read in thread and notify this class.
    """

    def __init__(self, buffer, updateFoo):
        self.guiUpdate = updateFoo
        self.buffer = buffer
        #self.is_paused = False

    #_ASYNC_ called from Notifier thread!
    #max ID 11b extended 29b
    def on_message_received(self, msg):
        # data to handle, will be added to master loop to work with
        if msg.arbitration_id > 0xFF: 
            pass #master.buffer.put(msg)
        # data to show, might wait, resolved in event called by GLib
        else: # > 0xFF                
            self.buffer.put(msg)
            GLib.idle_add(self.guiUpdate)

class CANutilser():
    def __init__(self, buffer, updateFoo):
        #initialize bus
        self.canbus = can.Bus(interface='socketcan',
                          channel= 'can0',
                          bitrate= '250000')

        self.canListener = CANListener(buffer, updateFoo)
        self.notifier = can.Notifier(self.canbus, [self.canListener])
        #vytvořit objekt který by měl builder a obsahoval funkce update pro CAN a Master?

    def write(self, data):
        msg = can.Message(arbitration_id = 2, data=data)
        print(str(msg))
        self.canbus.send(msg, timeout=0.2)

    def shortMessage(self, msg):
        data_string = []
        for index in range(0, min(msg.dlc, len(msg.data))):
                data_string.append("{0:02x}".format(msg.data[index]))
        return ("ID:{} | DATA:{}".format(hex(msg.arbitration_id), str(data_string)))

class Master:
    def __init__(self, buffer, writer, updater):
        self._running = True
        self._thread = threading.Thread(target = self.loop,
                                        daemon = True,
                                        name = "WorkerThread")
        self._thread.start()
    
    def stop(self, timeout):
        self._running = False
        if self._thread.is_alive():
            self._thread.join(timeout)

    def loop(self):
        while True:
            time.sleep(1)

    def worker(self, part, count):
        for i in range(count):
            pass
    
#msg types 
#07 command - adres 2 do 4, val 6 (i dont read)
#70 return - adres 2 task 4 val hotovo
#700 info - error 4

class Handler:
    def __init__(self, builder, writer):
        self.builder = builder
        self.write = writer

    def on_window1_destroy(self, *args):
        Gtk.main_quit()

    def on_button1_clicked(self, button):
        uinput = self.builder.get_object("input1").get_text().split(",")
        uinput = [int(i) for i in uinput]
        self.write(uinput)

#nemel by byt staticky nebo tak neco? singleton?
class App:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("/home/pi/Code/tryPy/gui.glade")
        self.updater = GUIupdater(self.builder)
        
        self.canBuffer = queue.Queue()
        self.masterBuffer = queue.Queue()
        #vytvořit objekt který by měl builder a obsahoval funkce update pro CAN a Master?
        self.can = CANutilser(self.canBuffer, self.updater.canUpdate)
        self.worker = Master(self.masterBuffer, self.can.write, self.updater.canUpdate)

        self.builder.connect_signals(Handler(self.builder, self.can.write))
        
        self.window = self.builder.get_object("window1")
        self.window.show_all()

        Gtk.main()

if __name__ == "__main__":
    gui = App()
