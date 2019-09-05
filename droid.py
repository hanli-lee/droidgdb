#!/usr/bin/python
# -*- coding: utf-8 -*- 
# author: hanli

import os
import sys
import commands
import subprocess

def usage():
    print "-------------------------------"
    print "   Usage:"
    print "       1.driod [core] [symdir] [core-file] [bin]"
    print "               *symdir, like       : ~/out/target/product/xxx/symbols/"
    print "               *core-file, like     : ~/LOG/core-HeapTaskDaemon-2806"
    print "               *bin, this arg is neccessary while debug a native process, like : dex2oat"
    print ""
    print "       2.droid [attach] [symdir] [pid/processName]"
    print "               $ droid attach ~/out/target/product/xxx/symbols/ zygote64"
    print "               both JAVA & NATIVE process supported now."
    print ""
    print "       3.droid [debug] [arm/arm64] [executable]"
    print "               $ droid debug arm64 hello"
    print "               not supported now."
    print ""
    print "       4.droid h"
    print "               print droid cmd history"
    print ""
    sys.exit()

#source_dir="/home/hanli/android_source_code/"

print '\n' + source_dir + '\n'

gdb = source_dir + "prebuilts/gdb/linux-x86/bin/gdb"
gdbserver32_path = source_dir + "prebuilts/misc/android-arm/gdbserver/gdbserver"
gdbserver64_path = source_dir + "prebuilts/misc/android-arm64/gdbserver64/gdbserver64"
gdbserver32 = "/data/local/tmp/gdbserver"
gdbserver64 = "/data/local/tmp/gdbserver64"

#CURRENT_DIR = os.path.abspath('.')
CURRENT_DIR = sys.path[0]

SCRIPT_FILE = CURRENT_DIR + "/gdb-script/init.gdb"
SCRIPT_FILE0 = CURRENT_DIR + "/art/command_file.py"
#SCRIPT_FILE1 = CURRENT_DIR + "/gdb-script/art_heap.gdb"
SCRIPT_FILE1 = CURRENT_DIR + "/art/command_file.py"
#SHADOW_FILE = CURRENT_DIR + "/shadow/gdb_driver.py"
SHADOW_FILE = CURRENT_DIR + "/shadow/gdb_driver.py"

if len(sys.argv) < 2:
    print 'No command specified.'
    usage()

def get_android_version():
    (result, output) = commands.getstatusoutput("adb shell getprop ro.build.version.release")
    if result == 0:
        return int(output[0:1])
    return 0

ANDROID_VERSION = int(0)


def get_pid_by_name(proc_name):
    ANDROID_VERSION = get_android_version()
    command = "adb shell ps | grep " + proc_name + "|grep -v \"$0\" |grep -v \"grep\" | awk \'{print $2}\'"
    if int(ANDROID_VERSION) >= 8:
        command = "adb shell ps -e | grep " + proc_name + "|grep -v \"$0\" |grep -v \"grep\" | awk \'{print $2}\'"
#    print "command: " + command
    (result, output) = commands.getstatusoutput(command)

    if result == 0:
        return output
    return -1

#ppid=`adb shell ps  | grep "$process"|grep -v "$0"|grep -v "grep"| awk '{print $3}'`
#ppid=`adb shell ps  | grep "$process"|grep -v "$0"|grep -v "grep"| awk '{FS=" "}{if ($2=='$process') print $3}'`
def get_proc_ppid(process):
    ANDROID_VERSION = get_android_version()
    command = "adb shell ps | grep " + process + "|grep -v \"$0\" | grep -v \"grep\" | "
    if int(ANDROID_VERSION) >= 8:
        command = "adb shell ps -e | grep " + process + "|grep -v \"$0\" | grep -v \"grep\" | "
    if process.isdigit() == True:
        command = command + "awk \'{FS=\" \"}{if ($2==\'" +process + "\') print $3}\'"
    else:
        command = command + "awk \'{print $3}\'"

    (r, out) = commands.getstatusoutput(command)
    return out

def get_proc_name(process):
    ANDROID_VERSION = get_android_version()
    command = "adb shell ps | grep " + process + "|grep -v \"$0\" | grep -v \"grep\" | "
    if int(ANDROID_VERSION) >= 8:
        command = "adb shell ps -e | grep " + process + "|grep -v \"$0\" | grep -v \"grep\" | "
    if process.isdigit() == True:
        command = command + "awk \'{FS=\" \"}{if ($2==\'" +process + "\') print $9}\'"        
    else:
        command = command + "awk \'{print $9}\'"
    (r, out) = commands.getstatusoutput(command)
    return out

def droid_init():
    (result, output) = commands.getstatusoutput('adb root')
    if result == 0:
        if 'adbd cannot run as root' in output:
            print '\n\n---ONLY ROOT COULD ATTACH PROCESS---\n\n'
            sys.exit()
        else:
            print '\n'
    else:
        print '\n\n---NO DEVICES/EMULATORS FOUND---\n\n'
        sys.exit()

    os.system('adb shell setenforce 0')
    child = subprocess.Popen('adb push ' + gdbserver32_path + ' ' + gdbserver32, shell=True, stdout=subprocess.PIPE)
    child.wait()
    child = subprocess.Popen('adb push ' + gdbserver64_path + ' ' + gdbserver64, shell=True, stdout=subprocess.PIPE)
    child.wait()


def droid_attach(symdir, process):
    if os.path.isdir(symdir) == False:
        print 'ERROR, symbols do not exist: ' + symdir
        sys.exit()

    droid_init()

    ANDROID_VERSION = get_android_version()

    print "Android version: " + str(ANDROID_VERSION)

    pid = process
    ppid = bytes(1)
    proc_name = process
    if process.isdigit():
        ppid = get_proc_ppid(process)
        proc_name = get_proc_name(process).split()
        if len(proc_name) < 1:
            print 'ERROR, No such process0: ' + process
            sys.exit()
    else:
        if len(process) < 1:
            print 'ERROR, you\'d better input a unique pid or process name\n\n'
            sys.exit()
        else:
            pid = get_pid_by_name(process)
#            print "pid: " + pid
            if len(pid.split()) > 1:
                print 'ERROR, there are more than one process match *' + process + "* ："
                print pid.split()
                print 'ERROR, you\'d better input a unique pid or process name\n'
                sys.exit()
            elif len(pid.split()) < 1:
                print 'ERROR, No such process1: ' + process
                sys.exit()
            ppid = get_proc_ppid(process)
            proc_name = get_proc_name(process).split()

    print "ppid: " + ppid + " proc_name： " + proc_name[0]
    parent = get_proc_name(ppid).split()

    print 'process: ' + proc_name[0] + ", pid(" + pid + "), parent(" + str(len(parent)) + ")"

    (r, link) = commands.getstatusoutput('adb shell readlink /proc/' + pid + '/exe')

    binary = (symdir + link).replace("//", "/").strip()
    bin_path = binary[0:binary.rfind("/") + 1]
    gdbserver = gdbserver32
    solib_path = (symdir + '/system/lib/').replace("//", "/")

    (r, out) = commands.getstatusoutput('file ' + binary)

    if '64-bit' in out:
        gdbserver = gdbserver64
        solib_path = (symdir + '/system/lib64/').replace("//", "/")
    elif '32-bit' not in out:
        print 'ERROR, unrecognized executable: ' + binary
        sys.exit()

    print "\n\ngdbserver:" + gdbserver + "\nbin_path: " + bin_path + "\nsolib:    " + solib_path + "\nbin:      " + binary + "\n\n\n"

    if os.path.isfile(binary) == False:
        print 'ERROR, binary: ' + binary + ', do not exist.'
        sys.exit()

    os.system('sleep 1')
    os.system('adb shell ' + gdbserver + ' :1234 --attach ' + pid + '&')
    os.system('adb forward tcp:1234 tcp:1234')
    os.system('sleep 1')
    print '\n\n\n'

    attach_cmd = gdb + " --ex=\"file "+ binary + "\" --ex=\"set sysroot " + symdir + "\" --ex=\"set solib-search-path " + solib_path + ':' + bin_path + "\" --ex=\"target remote localhost:1234\" --ex=\"dir " + source_dir + "\" --ex=\"set print pretty on\" --ex=\"source " + SCRIPT_FILE + "\" --ex=\"source " + SCRIPT_FILE0 + "\" --ex=\"source " + SCRIPT_FILE1 + "\" --ex=\"source " + SHADOW_FILE + "\" --ex=\"bt\" --ex=\"setandroid_version " + str(ANDROID_VERSION) + "\" --ex=\"get_android_version\""

    os.system(attach_cmd)

def record_command(command):
    history_filepath = CURRENT_DIR + '/.droid_history.txt'
    h_file = file(history_filepath, 'a+')

    recorded = False

    while True:
        line = h_file.readline()
        if len(line) == 0:
            break
        if line.strip('\n') == command.strip('\n'):
            recorded = True
            break

    if recorded == False:
        h_file.write(command + '\n')

    h_file.close()
    
def droid_core(symdir, coredump, binary=None):

    if (os.path.isdir(symdir) == False or os.path.isfile(coredump) == False):
        print 'ERROR, symbols or coredump do not exist.'
        print 'symbols: ' + symdir
        print 'corefile:' + coredump
        sys.exit()

    droid_cmd = 'droid core ' + os.path.abspath(symdir) + ' ' + os.path.abspath(coredump)

    (r, out) = commands.getstatusoutput('file ' + coredump)
    
    bin_path = symdir + '/system/bin/'
    bin_path2 = symdir + '/system/xbin/'
    solib_path = symdir + '/system/lib/'

    if binary == None:
        if '64-bit' in out:
            binary = bin_path + 'app_process64'
            solib_path = symdir + '/system/lib64/'
        elif '32-bit' in out:
            binary = bin_path + 'app_process32'
        else:
            print 'ERROR, unrecognized core file: ' + coredump
            sys.exit()
    else:
        droid_cmd = droid_cmd + ' ' + os.path.abspath(binary)
        tmp_binary = bin_path + binary
        if os.path.isfile(tmp_binary) == False:
            print 'ERROR, binary: ' + tmp_binary + ', do not exist.'
            binary = bin_path2 + binary
            if os.path.isfile(binary) == False:
                print 'ERROR, binary: ' + binary + ', do not exist.'
                sys.exit()
        else:
            binary = tmp_binary

        if '64-bit' in out:
            solib_path = symdir + '/system/lib64/'
        elif '32-bit' in out:
            solib_path = symdir + '/system/lib/'
        else:
            print 'ERROR, unrecognized core file: ' + coredump

    record_command(droid_cmd)
    binary = binary.replace("//", "/")
    bin_path = bin_path.replace("//", "/")
    solib_path = solib_path.replace("//", "/")

    print os.path.abspath(bin_path)
    print os.path.abspath(solib_path)
    print os.path.abspath(binary)
    print os.path.abspath(coredump)
    print '\n\n\n'
    

    core_cmd = gdb + " --ex=\"file "+ binary + "\" --ex=\"set sysroot " + symdir + "\" --ex=\"set solib-search-path " + solib_path + ':' + bin_path + "\" --ex=\"core-file " + coredump + "\" --ex=\"dir " + source_dir + "\" --ex=\"set print pretty on\" --ex=\"source " + SCRIPT_FILE + "\" --ex=\"source " + SCRIPT_FILE0 + "\" --ex=\"source " + SCRIPT_FILE1 + "\" --ex=\"source " + SHADOW_FILE + "\" --ex=\"bt\" --ex=\"get_android_version\""

    os.system(core_cmd)

    pass

def show_history():
    history_filepath = CURRENT_DIR + '/.droid_history.txt'

    if os.path.isfile(history_filepath) == False:
        print '      No command recorded.\n'
        return
    h_file = file(history_filepath, 'r')

    index = 1
    while True:
        line = h_file.readline()
        if len(line) == 0:
            break
        if '!' in line:
            line = line.replace("!", "\!")
        print bytes(index) + '. ' + line
        index = index + 1

    print ''
    h_file.close()

if sys.argv[1] == 'core':
    if len(sys.argv) < 4:
        usage()
    elif len(sys.argv) == 4:
        droid_core(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 5:
        droid_core(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print 'droid core max parameter count is 5'
        usage()
elif sys.argv[1] == 'attach':
    if len(sys.argv) < 4:
        usage()
    elif len(sys.argv) == 4:
        droid_attach(sys.argv[2], sys.argv[3])
    else:
        print 'droid attach max parameter count is 4'
        usage()
elif sys.argv[1] == 'debug':
    if len(sys.argv) < 4:
        usage()
elif sys.argv[1] == '-h':
    usage()
elif sys.argv[1] == 'h':
    print 'command history:\n'
    show_history()
else:
    print 'ERROR, unrecognized command.'
    usage()

# adb forward tcp:12345 jdwp:pid
# jdb -attach localhost:12345
# clasess
# methods class
# stop in/at
# next
# step
# run
# where
# print
# dump
# locals
# clear
# cont

# adb tcpip 3435
# adb connect phoneip:3435
