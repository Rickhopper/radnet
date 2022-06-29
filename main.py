import json
from os import path
from tkinter import messagebox
import types
import socket
import threading
import selectors
from dataclasses import dataclass, field
import string
import PIL
from PIL import Image, ImageFont, ImageDraw
import tkinter as tk
from playsound import playsound
import dill as pickle

events = selectors.EVENT_READ | selectors.EVENT_WRITE

network_devices = []
devices = []  # Array of device class instances
prev_devices = {}

alarm_level = 2000
alarmEnabled = True

class Device:
    deviceAddr = ''
    data = []
    image = tk.Image
    deviceName = ''

    def __init__(self, addr, name):
        self.deviceAddr = addr
        self.deviceName = name
        self.data = []

    def get_name(self):
        return self.deviceName

    def set_name(self, Name):
        self.deviceName = Name

    def get_addr(self):
        return self.deviceAddr

    def append_data(self, data):
        self.data.append(data)


def find_device_index(address):
    global devices
    remove = string.punctuation + string.whitespace

    for i in devices:
        if (str(devices[devices.index(i)].get_addr())).translate(remove) == str(address).translate(remove):
            return devices.index(i)
    #print("Device not found in connected devices")
    return -1


def loadPriorInfo():
    global prev_devices
    file_names = 'names_save.pk1'

    with open(file_names, "rb") as n:
        prev_devices = pickle.load(n)


def updateSeenDevice(address):
    global devices
    global prev_devices
    remove = string.punctuation + string.whitespace

    for k, v in prev_devices.items():
        if (str(k).translate(remove) == str(address).translate(remove)):
            # print("Device found!")
            #print(find_device_index(address))
            devices[find_device_index(address)].set_name(str(v))
        else:
            #print("Device not found!")
            pass



def server_thread():
    def accept_wrapper(sock):
        conn, addr = sock.accept()  # Should be ready to read

        # print("Address stored in device: " + str(addr))
        '''
        for i in devices:
            print(devices[devices.index(i)].get_addr())
        '''
        # gauge_creator(0, find_device_index(addr))

        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        sel.register(conn, events, data=data)

    def service_connection(key, mask):
        sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(1024)  # Should be ready to read
            print(recv_data)
            try:
                y = json.loads(recv_data.decode("utf-8"))
            except: y=[0,0]

            print(y[1])
            int_data = y[1]
            device_id = str(y[0])

            if device_id>str(0):
                if find_device_index(device_id)<0:
                    devices.append(Device(device_id,device_id ))
                updateSeenDevice(device_id)

                gauge_creator(int_data, find_device_index(device_id))
                devices[find_device_index(device_id)].append_data(int_data)

            # print("Received: " + str(int_data))

            '''
            for i in devices:   
                print(devices[devices.index(i)].data)
            '''

            if recv_data:
                out=1
                data.outb =out.to_bytes(1, "big")
                #data.outb += recv_data
            else:
                sel.unregister(sock)
                sock.close()
                #devices.pop(find_device_index(data.addr))

        if mask & selectors.EVENT_WRITE:
            if data.outb:
                # print(devices[0].data);
                # print('echoing', repr(data.outb), 'to', data.addr)
                sent = sock.send(data.outb)  # Should be ready to write    can this go!!!!!!!!
                data.outb = data.outb[sent:]
                pass

    sel = selectors.DefaultSelector()

    host = '0.0.0.0'
    port = 65432  # Port to listen on (non-privileged ports are > 1023)
    # print('Thread works')

    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.bind((host, port))
    lsock.listen()
    print('listening on', (host, port))
    lsock.setblocking(False)
    sel.register(lsock, selectors.EVENT_READ, data=None)

    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept_wrapper(key.fileobj)
            else:
                service_connection(key, mask)


def gauge_creator(gaugeinfo, gaugenumber):
    percent = gaugeinfo  # Percent for gauge
    # X and Y coordinates of the center bottom of the needle starting from the top left corner
    #   of the image
    x = 825
    y = 825
    loc = (x, y)
    # percent = percent / 100
    rotation = 99 - (0.036 * (gaugeinfo))  # 180 degrees because the gauge is half a circle
    # rotation = -9 # Factor in the needle graphic pointing to 50 (90 degrees)
    # print(rotation)
    dial = Image.open('needle.png')
    dial = dial.rotate(rotation, resample=PIL.Image.BICUBIC, center=loc)  # Rotate needle
    gauge = Image.open('gauge3.png')

    if gaugeinfo > alarm_level:
        alarm_img = Image.open('alarm_image.png')
        gauge.paste(alarm_img, mask=alarm_img)

    gauge.paste(dial, mask=dial)  # Paste needle onto gauge
    # image size
    size = (240, 145)
    # resize image
    out = gauge.resize(size)
    # save resized image
    file_name = "disp_gauge" + str(gaugenumber)
    out.save(file_name + '.png')
    image = Image.open(file_name + '.png')
    draw = ImageDraw.Draw(image)
    # font = ImageFont.load_default()
    font = ImageFont.truetype("Gidole-Regular.ttf", size=14)
    draw.text((100, 125), str(gaugeinfo) + 'CPM', font=font, align="center", fill="white")
    image.save(file_name + '.png')


def alarm():
    global alarmEnabled
    # print(int(alarmEnabled))
    if (alarmEnabled):
        for i in range(0, len(devices)):
            if (len(devices[i].data) > 0 and devices[i].data[-1] > alarm_level):
                playsound('sound.wav', block=False)
                #print("no sound")
        else:
            pass


class MenuBar(tk.Menu):
    def __init__(self, parent):
        tk.Menu.__init__(self, parent)
        fileMenu = tk.Menu(self, tearoff=False)
        self.add_cascade(label="Settings", underline=0, menu=fileMenu)
        fileMenu.add_command(label="User Options", underline=1, command=options)


class options():
    def __init__(self):
        top = tk.Toplevel()
        top.title("User Options")
        canvas2 = tk.Canvas(top, width=1000, height=600)
        bkg = tk.PhotoImage(file='atom2.png')
        canvas2.pack()

        options = ["No connected devices."]

        if (len(devices) > 0):
            options = []
            for i in devices:
                options.append(devices[devices.index(i)].get_name())

        selection = tk.StringVar()
        selection.set("Select Device")

        drop = tk.OptionMenu(canvas2, selection, *options)
        drop.pack()
        canvas2.create_window(260, 150, window=drop)

        nameLabel = tk.Label(canvas2, fg='gray10', text="Change Device ID: ", font=("Raleway", 11))
        nameLabel.pack()
        canvas2.create_window(116, 150, window=nameLabel)

        newName = tk.StringVar()
        newNameEntry = tk.Entry(canvas2, width=25, fg='gray10', textvariable=newName)
        newNameEntry.insert(0, "Enter new name here")
        newNameEntry.pack()
        canvas2.create_window(435, 150, window=newNameEntry)

        nameButton = tk.Button(canvas2, text="Save", fg='gray10', command=lambda: getNameInput(newName))
        nameButton.pack()
        canvas2.create_window(550, 150, window=nameButton)

        labelAlarm = tk.Label(canvas2, fg='gray10', text="Alarm level:", font=("Raleway", 11))
        labelAlarm.pack()
        canvas2.create_window(90, 100, window=labelAlarm)

        buttonAlarm = tk.Button(canvas2, text="Save", fg='gray10', command=lambda: getTextInput(alarm_val))
        buttonAlarm.pack()
        canvas2.create_window(330, 100, window=buttonAlarm)

        global alarm_level
        alarm_val = tk.StringVar(value=alarm_level)
        entry = tk.Entry(canvas2, width=25, fg='gray10', textvariable=alarm_val)
        entry.pack()
        canvas2.create_window(215, 100, window=entry)

        global alarmEnabled
        alarmEnabledCheck = tk.IntVar(value=(int(alarmEnabled)))
        alarmSound = tk.Checkbutton(canvas2, text="Enable/Disable Alarm Sound", font=("Raleway", 11),
                                    variable=alarmEnabledCheck, command=lambda: getSoundCheckbox(alarmEnabledCheck))
        alarmSound.pack()
        canvas2.create_window(470, 100, window=alarmSound)

        buttonClearData = tk.Button(canvas2, text="Clear Stored Device Names", fg='gray10',
                                    command=lambda: deleteData())
        buttonClearData.pack()
        canvas2.create_window(125, 200, window=buttonClearData)

        def getTextInput(text):
            global alarm_level
            result = entry.get()
            alarm_level = int(result)
            tk.messagebox.showinfo('Changed', 'Alarm level is now set to: ' + str(alarm_level))
            top.lift()

        def getSoundCheckbox(check):
            global alarmEnabled
            alarmEnabled = bool(check.get())

        def getNameInput(text):
            global devices
            global prev_devices
            remove = string.punctuation + string.whitespace
            newName = newNameEntry.get()
            oldName = str(selection.get()).translate(remove)

            for i in devices:
                if (str(devices[devices.index(i)].get_name())).translate(remove) == oldName:
                    devices[devices.index(i)].set_name(str(newName))

                    for k, v in prev_devices.items():
                        if v == oldName:
                            prev_devices[k] = newName

                    tk.messagebox.showinfo('Changed', 'Device "' + str(
                        devices[devices.index(i)].get_addr()) + '" now known as "' + str(
                        devices[devices.index(i)].get_name()))

            top.lift()

            #print(selection.get())
            #print("Device at index: " + str(find_device_index(selection.get())) + "'s name is now: " + str(
                #devices[find_device_index(selection.get())].get_name()))

        def deleteData():

            if (tk.messagebox.askyesno('Verify', 'Continue? All stored device names will be erased')):
                global devices
                global prev_devices
                prev_devices.clear()
                file_names = "names_save.pk1"
                empty_data = {}

                for i in devices:
                    devices[devices.index(i)].set_name(devices[devices.index(i)].get_addr())

                with open(file_names, "wb") as n:
                    pickle.dump(empty_data, n, protocol=pickle.HIGHEST_PROTOCOL)

                tk.messagebox.showinfo('Deleted', 'All device names have been reset')
            else:
                pass

            top.lift()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        menubar = MenuBar(self)
        self.config(menu=menubar)
        self.title('Radiation Monitoring Station')
        self.photo = tk.PhotoImage(file="radiation.png")
        self.iconphoto(False, self.photo)
        self.canvas = tk.Canvas(self, width=1650, height=856)
        self.canvas.configure(bg='black')
        self.bkg = tk.PhotoImage(file='atom3.png')
        self.canvas.create_image(700, 428, image=self.bkg)
        self.title1 = tk.PhotoImage(file='titlebar.png')
        self.canvas.create_image(800, 50, image=self.title1)
        self.canvas.pack()
        self.draw()

    def draw(self):

        alarm()

        try:
            self.canvas.delete('con_dev_text')
        except:
            pass

        self.con_devicesText = self.canvas.create_text(800, 100, text='Connected Devices: ' + str(len(devices)),
                                                       fill="gray10", font=('Helvetica 15 bold'), tag='con_dev_text')

        for i in devices:
            while (True):  # Try statement to avoid image loading up errors and app crashing
                try:
                    self.img = tk.PhotoImage(file='disp_gauge' + str(devices.index(i)) + '.png')
                    # self.img = tk.PhotoImage(file='png')
                    devices[devices.index(i)].image = self.img

                    if (len(devices) <= 5):
                        self.gauge = self.canvas.create_image(250 * (devices.index(i) + 1), 250,
                                                              image=devices[devices.index(i)].image)
                        try:
                            self.canvas.delete('nameText' + str(devices.index(i)))
                        except:
                            continue

                        self.canvas.create_text(250 * (devices.index(i) + 1), 350,
                                                text=(str(devices[devices.index(i)].get_name())), fill="gray10",
                                                font=('Helvetica 15 bold'), tag=('nameText' + str(devices.index(i))))

                    else:
                        if (devices.index(i) < 5):
                            self.gauge = self.canvas.create_image(250 * (devices.index(i) + 1), 250,
                                                                  image=devices[devices.index(i)].image)
                            try:
                                self.canvas.delete('nameText' + str(devices.index(i)))
                            except:
                                continue

                            self.canvas.create_text(250 * (devices.index(i) + 1), 350,
                                                    text=(str(devices[devices.index(i)].get_name())), fill="gray10",
                                                    font=('Helvetica 15 bold'),
                                                    tag=('nameText' + str(devices.index(i))))
                        else:
                            self.gauge = self.canvas.create_image(250 * (devices.index(i) - 4), 500,
                                                                  image=devices[devices.index(i)].image)
                            try:
                                self.canvas.delete('nameText' + str(devices.index(i)))
                            except:
                                continue
                            self.canvas.create_text(250 * (devices.index(i) - 4), 600,
                                                    text=(str(devices[devices.index(i)].get_name())), fill="gray10",
                                                    font=('Helvetica 15 bold'),
                                                    tag=('nameText' + str(devices.index(i))))

                except:
                    continue
                else:
                    break
        self.after(1000, self.draw)

    def on_closing(self):

        global devices
        file_names = "names_save.pk1"
        devices_store = {}

        with open(file_names, "rb") as n:
            devices_store = pickle.load(n)

        for i in devices:
            devices_store[devices[devices.index(i)].get_addr()] = devices[devices.index(i)].get_name()

        with open(file_names, "wb") as n:
            pickle.dump(devices_store, n, protocol=pickle.HIGHEST_PROTOCOL)

        self.destroy()


def main():
    server = threading.Thread(target=server_thread)
    server.daemon = True
    server.start()

    loadPriorInfo()
    playsound('sound.wav', block=False)

    print(prev_devices)
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
    playsound('sound.wav', block=False)

if __name__ == '__main__':
    main()
