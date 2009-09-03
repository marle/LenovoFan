#!/usr/bin/python
#encoding:UTF-8
#
#    LenovoFan to set fan speed for Lenovo SL laptop series.
#    Copyright (C) 2009  Marcin Lewandowski (nicram.el@gmail.com)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
import os
import sys
import gtk
import gobject
import pynotify

class Sensors:
    
    fan = None
    cpu = '/sys/devices/LNXSYSTM:00/LNXTHERM:00/LNXTHERM:01/thermal_zone/temp'
    rpm = {1500: "70", 1800: "82", 2100: "96", 2400: "111", 2700: "127"}
    enabled = False
    
    def __init__(self):
        if not os.path.exists(self.cpu):
            print 'Cannot read CPU temperature'
            sys.exit()
        
        for root, dirs, files in os.walk('/sys/devices/platform/lenovo-sl-laptop/hwmon/'):
            if 'fan1_input' in files:
                self.fan = root + '/'
        if not self.fan:
             print 'cannot find sensors'
             sys.exit()

    def readFan(self):
        return int(open(self.fan + 'fan1_input').read().strip())

    def readCpu(self):
        return int(open(self.cpu).read().strip()[:-3])

    def enableFanControl(self, enable):
        if not enable and self.enabled:
            self.writeFan(2700)
        file = open(self.fan + 'pwm1_enable', 'w')
        file.write("1" if enable else "0")
        file.close()
        self.enabled = enable
    
    def writeFan(self, value):
        if not value in self.rpm:
            print 'Unknown rpm', value
            return False
        if not self.enabled:
            self.enableFanControl(True)
        print self.rpm[value]
        file = open(self.fan + 'pwm1', 'w')
        file.write(self.rpm[value])
        file.close()
        return True

class PopupMenu:
    
    def __init__(self, lenovoFan):
        
        self.auto = gtk.RadioMenuItem(None, 'Auto', True)
        self.off = gtk.RadioMenuItem(self.auto, 'Bios control', True)
        self.exit = gtk.MenuItem('Exit', True)
        
        self.exit.connect('activate', lenovoFan.exit)
        self.auto.connect('activate', lenovoFan.auto)
        self.off.connect('activate', lenovoFan.off)

        self.menu = gtk.Menu()
        for rpm in sorted(lenovoFan.sensors.rpm):
            item = gtk.RadioMenuItem(self.auto, str(rpm) + ' rpm', True)
            item.connect('activate', lenovoFan.rpm, rpm)
            self.menu.append(item)
        self.menu.append(self.auto)
        self.menu.append(self.off)
        self.menu.append(gtk.SeparatorMenuItem())
        self.menu.append(self.exit)
        self.menu.show_all()
        
        self.bios()

    def bios(self):
        self.off.set_active(True)

    def show(self, button, time):
        self.menu.popup(None, None, None, button, time)

class LenovoFan:

    title = 'LenovoFan'

    def __init__(self):
        self.sensors = Sensors()
        self.eventbox = gtk.EventBox()
        pixbuf = gtk.gdk.pixbuf_new_from_file(sys.path[0] + '/turbine.png').scale_simple(24, 24, gtk.gdk.INTERP_BILINEAR)
        
        self.tray = gtk.StatusIcon()
        self.tray.set_from_pixbuf(pixbuf)
        self.tray.connect('popup-menu', self.popup)
        self.tray.connect('activate', self.status)
        
        self.popup_menu = PopupMenu(self)
        
        if not pynotify.init("LenovoFan"):
            print "pynotify.init failed"
        
        while gtk.events_pending():
            gtk.main_iteration(True)
        
        self.check()
        self.maintimer = gobject.timeout_add(10000, self.check)
        
    def status(self, icon):
        if hasattr(self, "notify"):
            self.notify.close()
        self.notify = pynotify.Notification(self.title, self.message, "dialog-info")
        self.notify.show()
        
    def popup(self, icon, button, time):
        self.popup_menu.show(button, time)
            
    def check(self):
        rpm = self.sensors.readFan()
        if rpm < 300:
            self.sensors.writeFan(2700)
            pynotify.Notification(self.title, "Fan not working. Setting speed to 2700 rpm.", "dialog-warning").show()
        temp = self.sensors.readCpu()
        if self.sensors.enabled and temp >= 65:
            self.sensors.enableFanControl(False)
            self.popup_menu.bios()
            pynotify.Notification(self.title, "CPU temperature: 65°C.\n\nSwitching to BIOS control.", "dialog-warning").show()
        self.message = 'CPU: ' + str(temp) + '°C\nFan: ' + str(rpm) + ' rpm'
        return True

    def auto(self, event):
        print 'not implemented'
        return True
        
    def off(self, event):
        self.sensors.enableFanControl(False)
        self.tray.set_tooltip('Bios control')
        return True

    def rpm(self, event, value):
        if self.sensors.writeFan(value):
            self.tray.set_tooltip(str(value) + ' rpm')
        return True

    def exit(self, event):
        self.sensors.enableFanControl(False)
        gtk.main_quit(0)

    def main(self):
        gtk.main()

if __name__ == "__main__":
    LenovoFan().main()
