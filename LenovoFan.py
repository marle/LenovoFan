#!/usr/bin/python
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
#
# Run is as root to allow changing fan speed. 
import os
import sys
import gtk
import gobject

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

    def enableFanControll(self, enable):
        if not enable and self.enabled:
            self.writeFan(2700)
        file = open(self.fan + 'pwm1_enable', 'w')
        file.write("1" if enable else "0")
        file.close()
        self.enabled = enable
        return
    
    def writeFan(self, value):
        if not value in self.rpm:
            print 'Unknown rpm', value
            return False
        if not self.enabled:
            self.enableFanControll(True)
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
            item = gtk.RadioMenuItem(self.auto, str(rpm) + 'rpm', True)
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
    
    tip = 'Lenovo SL Series Fan control'
    
    def __init__(self):
        self.sensors = Sensors()
        self.eventbox = gtk.EventBox()
        pixbuf = gtk.gdk.pixbuf_new_from_file(sys.path[0] + '/turbine.png').scale_simple(24, 24, gtk.gdk.INTERP_BILINEAR)
        
        self.tray = gtk.StatusIcon()
        self.tray.set_from_pixbuf(pixbuf)
        self.tray.connect('popup-menu', self.popup)
        
        self.popup_menu = PopupMenu(self)
        
        while gtk.events_pending():
            gtk.main_iteration(True)
            
        self.maintimer = gobject.timeout_add(5000, self.check)
        
    def popup(self, icon, button, time):
        self.popup_menu.show(button, time)
            
    def check(self):
        temp = self.sensors.readCpu()
        if temp > 65:
            self.sensors.enableFanControll(False)
            self.popup_menu.bios()
            self.tray.set_tooltip(self.tip + '\nSafety warning: bios control enabled')
        return True

    def auto(self, event):
        print 'not implemented'
        return True
        
    def off(self, event):
        self.sensors.enableFanControll(False)
        self.tray.set_tooltip(self.tip)
        return True

    def rpm(self, event, value):
        if self.sensors.writeFan(value):
            self.tray.set_tooltip(self.tip + '\nSet to ' + str(value) + 'rpm')
        return True

    def exit(self, event):
        self.sensors.enableFanControll(False)
        gtk.main_quit(0)

    def main(self):
        gtk.main()

if __name__ == "__main__":
    print 'starting...'
    LenovoFan().main()