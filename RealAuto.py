# -----------------------------------------------------------------------------
# Title       : RealAuto.py
# Author      : AugGust
# Date        : 5-Jun-2020
# Description : More Realistic Automatic Gearbox
# -----------------------------------------------------------------------------

import ac
import acsys
import math
import time
import threading
import configparser
import os
import platform
import sys

if platform.architecture()[0] == "64bit":
	sysdir = os.path.dirname(__file__)+'/stdlib64'
else:
	sysdir = os.path.dirname(__file__)+'/stdlib'

sys.path.insert(0, sysdir)
os.environ['PATH'] = os.environ['PATH'] + ";."

import keyboard

#sim info stuff
from sim_info import info

maxRPM = 0
gear = 0
gas = 0
brake = 0
steerAngle = 0
rpm = 0
speed = 0
slipping = False

initialized = False
measureIdleTime = 99999999999999


maxShiftRPM = 0
idleRPM = 0

rpmRangeSize = 0
rpmRangeTop = 0
rpmRangeBottom = 0

lastShiftTime = 0
lastShiftUpTime = 0
lastShiftDownTime = 0

#0 is eco normal driving, 4 is max
aggressiveness = 0
aggr_lbl = 0
last_inc_aggr_time = 0

# the default driving mode is : Manual (no automatic shifting)
drive_mode = 0

mode_button = 0

# initialize the App's GUI controls 
# (allowing to change driving modes)
def acMain(ac_version):
    global aggr_lbl, mode_button
    app_window = ac.newApp("Realistic Auto")
    ac.setSize(app_window, 180, 210)

    mode_label = ac.addLabel(app_window, "Drive Mode")
    ac.setFontAlignment(mode_label, "center")
    ac.setPosition(mode_label, 90, 40)

    mode_button = ac.addButton(app_window, "Manual")
    ac.setPosition(mode_button, 30, 65)
    ac.setSize(mode_button, 120, 25)
    ac.addOnClickedListener(mode_button, toggleDriveMode)

    debug_lbl = ac.addLabel(app_window, "Debug Info")
    ac.setPosition(debug_lbl, 20, 110)
    aggr_lbl = ac.addLabel(app_window, "")
    ac.setPosition(aggr_lbl, 20, 135)
    initializeInfo()
    return

# infinite loop to update the decision algorithm
# and actually decide if we need to take any action right now
def acUpdate(deltaT):
    getInfo()
    # only run the algorithm if we are not in manual mode (don't waste CPU cycles)
    if drive_mode > 0:
        analyzeInput(deltaT)
        makeDecision()

# define the available driving modes
modes = ["Manual", "Auto: Normal", "Auto: Sport", "Auto: Eco"]


def toggleDriveMode(*args):
    global mode_button, drive_mode
    drive_mode += 1
    drive_mode = drive_mode%4
    ac.setText(mode_button, modes[drive_mode])


# define the settings for different driving modes
# 0 index is : used in agressiveness increase decision
# 1 index is : used in agressiveness increase decision
# 2 index is : how quickly the aggressiveness lowers when driving calmly (1/value)
# 3 index is : the bare minimum aggressiveness to keep at any given time
gas_thresholds =    [[0, 0, 0, 0],#manual
                    [0.95, 0.4, 12, 0.15],# auto: normal
                    [0.8, 0.4, 24, 0.5],# auto: sport
                    [1, 0.5, 6, 0]]# auto: eco


def analyzeInput(deltaT):
    # add brake force, and consider brake force exactly as gas input
    global aggressiveness, aggr_lbl, rpmRangeTop, rpmRangeBottom, last_inc_aggr_time
    # compute a new aggressiveness level depending on the gas and brake pedal pressure
    # and apply a factor from the current driving mode
    new_aggr = min(
        1, 
        max((
            gas - gas_thresholds[drive_mode][1]
        ) / 
        (
           gas_thresholds[drive_mode][0] - gas_thresholds[drive_mode][1]
        ),
        (
            brake - (gas_thresholds[drive_mode][1] - 0.3)
        ) / 
        (
           gas_thresholds[drive_mode][0] - gas_thresholds[drive_mode][1]
        )*1.6)
    )
    # new_aggr = min(1, (gas - gas_thresholds[drive_mode][1]) / (gas_thresholds[drive_mode][0] - gas_thresholds[drive_mode][1]))
    # ex full accel: 1, (1 - 0.95) / (0.95 - 0.4)
    # 1, 0.05 / 0.55 = 0.09

    # if the newly computed agressiveness is higher than the previous one
    if new_aggr > aggressiveness and gear > 0:
        # we update it with the new one
        aggressiveness = new_aggr
        # and save the time at which we updated it
        last_inc_aggr_time = time.time()

    # if we have not increased the agressiveness for at least 2 seconds
    if time.time() > last_inc_aggr_time + 2:
        # we lower the aggressiveness by a factor given by the current driving move
        aggressiveness -= (deltaT / gas_thresholds[drive_mode][2])

    # we maintain a minimum aggressiveness defined by the current driving mode
    # it's only used by the sport mode, to maintain the aggressiveness always above 0.5
    # all other driving modes will use the actual computed aggressiveness 
    # (which can be bellow 0.5)
    aggressiveness = max(
        aggressiveness, 
        gas_thresholds[drive_mode][3]
    )

    # adjust the allowed upshifting rpm range, 
    # depending on the aggressiveness
    rpmRangeTop = (
        idleRPM + 1000 + 
        (
            (maxShiftRPM - idleRPM - 1000)
            *aggressiveness
        )
    )
    # adjust the allowed downshifting rpm range, 
    # depending on the aggressiveness
    rpmRangeBottom = max(
        idleRPM + (min(gear, 6) * 80), 
        rpmRangeTop - rpmRangeSize
    )

    # update the App's displayed text with : 
    # current rpm ranges, and current aggressiveness
    ac.setText(
        aggr_lbl, 
        "Aggressiveness: " + 
        str(round(aggressiveness, 2)) + 
        "\nRpm Top: " + 
        str(round(rpmRangeTop)) + 
        "\nRpm Bottom: " + 
        str(round(rpmRangeBottom)))
    
# this is where we decide if we want to shift
def makeDecision():
    if (
        # we have already shifted in the last 0.1s
        time.time() < lastShiftTime + 0.1 or 
        # or we are in neutral
        gear < 1 or 
        # or we have already shifted up in the last 1 sec
        time.time() < lastShiftUpTime + 1 or 
        # or we have already shifted down in the last 2 sec
        time.time() < lastShiftDownTime + 2
    ):
        # do not change gear
        return
    if (
        # we have reached the top range (upshift are rpm-allowed)
        rpm > rpmRangeTop and 
        # we don't have wheel spin
        not slipping and 
        # we have not downshifted in the last 1 sec (to prevent up-down-up-down-up-down)
        time.time() > lastShiftDownTime + 1
    ):
        # actually UPSHIFT
        shiftUp()
    elif (
        # we have reached the lower rpm range (downshift are rpm-allowed)
        rpm < rpmRangeBottom and 
        # we don't have wheel spin
        not slipping and 
        # we are not in first gear (meaning we have gears available bellow us)
        gear > 1 and 
        # we have not downshifted in the last 2 sec
        time.time() > lastShiftDownTime + 2
    ):
        # actually DOWNSHIFT
        shiftDown()


# retrieve contextual car info from AC (gas, brake, gear, slip), 
# and put them into readily available variables
def getInfo():
    global gear, gas, brake, steerAngle, rpm, speed, slipping
    if not initialized:
        initializeInfo()
    gear = ac.getCarState(0,acsys.CS.Gear) - 1
    gas = ac.getCarState(0,acsys.CS.Gas)
    brake = ac.getCarState(0,acsys.CS.Brake)
    # we must also retrieve the steerAngle here (not sure about var naming)
    # steerAngle = ac.getCarState(0,acsys.CS.SteerAngle)
    rpm = ac.getCarState(0,acsys.CS.RPM)
    speed = ac.getCarState(0,acsys.CS.SpeedKMH)

    maxSlip = ac.getCarState(0,acsys.CS.NdSlip)[0]
    if ac.getCarState(0,acsys.CS.NdSlip)[1] > maxSlip:
        maxSlip = ac.getCarState(0,acsys.CS.NdSlip)[1]
    if ac.getCarState(0,acsys.CS.NdSlip)[2] > maxSlip:
        maxSlip = ac.getCarState(0,acsys.CS.NdSlip)[2]
    if ac.getCarState(0,acsys.CS.NdSlip)[3] > maxSlip:
        maxSlip = ac.getCarState(0,acsys.CS.NdSlip)[3]
    if maxSlip > 1:
        slipping = True
    else:
        slipping = False


def initializeInfo():
    global maxRPM, maxShiftRPM, measureIdleTime, idleRPM, initialized, rpmRangeSize
    if not (info.static.maxRpm == 0):
        maxRPM = info.static.maxRpm
        maxShiftRPM = maxRPM * 0.95
        if measureIdleTime == 99999999999999:
            measureIdleTime = time.time() + 3
    
    if not initialized:
        if time.time() > measureIdleTime:
            idleRPM = ac.getCarState(0,acsys.CS.RPM)
            rpmRangeSize = (maxRPM - idleRPM)/3
            initialized = True

# fake pressing the P key, 
# trigerring an upshifting if the key is properly mapped in AC
def shiftUp():
    global lastShiftTime, lastShiftUpTime
    # actually press the key
    keyboard.press_and_release('p')
    # update the last shifting times
    lastShiftTime       = time.time()
    lastShiftUpTime     = time.time()

# fake pressing the O key, 
# trigerring a downshift if the key is properly mapped in AC
def shiftDown():
    global lastShiftTime, lastShiftDownTime
    # actually press the key
    keyboard.press_and_release('o')
    # update the last shifting times
    lastShiftTime       = time.time()
    lastShiftDownTime   = time.time()