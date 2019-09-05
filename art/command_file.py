#!/usr/bin/python                                                                                                                                                                       
# -*- coding: utf-8 -*- 
# author: hanli

import os
import gdb
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from art_class import Art_Class
from art_method import Art_Method
from art_thread import Art_Thread
from android_runtime import AndroidRuntime
from art_thread_list import Art_Thread_List
from art_global import Art_Global
from art_object import Art_Object

def CHECK_ANDROID_VERSION():
    version = int(AndroidRuntime.getAndroidVersion())
    if version < 6:
        print ""
        print "           **************************************************************************"
        print "           * Please set exact android version before use art script:                *"
        print "           * Example:                                                               *"
        print "           *    (gdb) setandroid_version 8                                          *"
        print "           *                                                                        *"
        print "           **************************************************************************"
        print ""
        return False
    return True

class SetAndroidVersion(gdb.Command):
    """set Android version.
    Usage: setandroid_version 6/7/8/9
    Example::
        (gdb) setandroid_version 7
    """

    def __init__(self):
        super(self.__class__, self).__init__("setandroid_version", gdb.COMMAND_USER)

    def invoke(self, args, from_tty):
        argv = gdb.string_to_argv(args)
        if len(argv) < 1:
            raise gdb.GdbError('This cmd need a [version num] arg.')
        AndroidRuntime.setAndroidVersion(argv[0])

SetAndroidVersion()

class GetAndroidVersion(gdb.Command):
    """get Android version.
    Example:
        (gdb) get_android_version
        Android Version: 8
    """

    def __init__(self):
        super(self.__class__, self).__init__("get_android_version", gdb.COMMAND_USER)

    def invoke(self, args, from_tty):
        argv = gdb.string_to_argv(args)
        if len(argv) > 0:
            raise gdb.GdbError('This cmd DO NOT need arg.')
        version = int(AndroidRuntime.getAndroidVersion())
        print ""
        print "           *****************************"
        print "           *    Android Version: " + str(version) + "     *"
        if version < 6:
            print "           **************************************************************************"
            print "           * Please set exact android version before use art script:                *"
            print "           * Example:                                                               *"
            print "           *    (gdb) setandroid_version 8                                          *"
            print "           *                                                                        *"
            print "           **************************************************************************"
        else:
            print "           *****************************"

GetAndroidVersion()

class PrintRuntime(gdb.Command):
    "print ART runtime instance."

    def __init__(self):
        super(self.__class__, self).__init__("art_print_runtime", gdb.COMMAND_USER)

    def invoke(self, args, from_tty):
        if CHECK_ANDROID_VERSION() == False:
            return
        argv = gdb.string_to_argv(args)
        if len(argv) > 0:
            raise gdb.GdbError('This cmd DO NOT need arg.')
        gdb.execute("p 'art::Runtime'::instance_")

PrintRuntime()

class ClassPrintName(gdb.Command):
    """print the descriptor of a class
    Usage: class_print_name class_addr
    Example:
        (gdb) class_print_name 0x13044660
    """
    def __init__(self):
        super(self.__class__, self).__init__("class_print_name", gdb.COMMAND_USER)

    def invoke(self, args, from_tty):
        if CHECK_ANDROID_VERSION() == False:
            return
        argv = gdb.string_to_argv(args)
        if len(argv) < 1:
            raise gdb.GdbError('This cmd NEED a class pointer.')
        art_class = Art_Class(argv[0])
        print art_class.get_name() + "    " + art_class.get_dex_location()

ClassPrintName()

class ObjectPrintName(gdb.Command):
    """
    Usage: object_print_name 0x13044660
    """
    def __init__(self):
        super(self.__class__, self).__init__("object_print_name", gdb.COMMAND_USER)

    def invoke(self, args, from_tty):
        if CHECK_ANDROID_VERSION() == False:
            return
        argv = gdb.string_to_argv(args)
        if len(argv) < 1:
            raise gdb.GdbError('This cmd NEED a object pointer.')
        art_object = Art_Object(argv[0])
        print art_object.get_detail_class_name()

ObjectPrintName()


class MethodPrintName(gdb.Command):
    """ print method's name
    Example:
        (gdb) method_print_name 0x13044660
    """
    def __init__(self):
        super(self.__class__, self).__init__("method_print_name", gdb.COMMAND_USER)

    def invoke(self, args, from_tty):
        if CHECK_ANDROID_VERSION() == False:
            return
        argv = gdb.string_to_argv(args)
        if len(argv) < 1:
            raise gdb.GdbError('This cmd NEED a method pointer.')
        art_method = Art_Method(argv[0])
        art_method.print_name()

MethodPrintName()

class ArtDecodeObject(gdb.Command):
    """ decode java object to real native object.
    Example:
        (gdb) art_decode_jobject 0x13044660
    """
    def __init__(self):
        super(self.__class__, self).__init__("art_decode_jobject", gdb.COMMAND_USER)

    def invoke(self, args, from_tty):
        if CHECK_ANDROID_VERSION() == False:
            return
        argv = gdb.string_to_argv(args)
        if len(argv) < 1:
            raise gdb.GdbError('This cmd NEED a method pointer.')
        art_thread_list = Art_Thread_List()
        if len(argv) == 2:
            print "real object: " + art_thread_list.decode_jobject(argv[0], argv[1])
        else:
            print "real object: " + art_thread_list.decode_jobject(argv[0])

ArtDecodeObject()

class ArtDumpThreadList(gdb.Command):
    """ dump art thread list.
    """
    def __init__(self):
        super(self.__class__, self).__init__("art_dump_thread_list", gdb.COMMAND_USER)

    def invoke(self, args, from_tty):
        if CHECK_ANDROID_VERSION() == False:
            return
        argv = gdb.string_to_argv(args)
        if len(argv) > 0:
            raise gdb.GdbError('This cmd DO NOT need arg.')
        art_thread_list = Art_Thread_List()
        art_thread_list.dump()

ArtDumpThreadList()

class ArtDumpThreadListWithMutex(gdb.Command):
    """ dump art thread list.
    """
    def __init__(self):
        super(self.__class__, self).__init__("art_dump_thread_list_with_mutex", gdb.COMMAND_USER)

    def invoke(self, args, from_tty):
        if CHECK_ANDROID_VERSION() == False:
            return
        argv = gdb.string_to_argv(args)
        if len(argv) > 0:
            raise gdb.GdbError('This cmd DO NOT need arg.')
        art_thread_list = Art_Thread_List()
        art_thread_list.dump(True)

ArtDumpThreadListWithMutex()

class ArtDumpDexCaches(gdb.Command):
    """ dump art thread list.
    """
    def __init__(self):
        super(self.__class__, self).__init__("art_dump_dexcaches", gdb.COMMAND_USER)

    def invoke(self, args, from_tty):
        if CHECK_ANDROID_VERSION() == False:
            return
        argv = gdb.string_to_argv(args)
        if len(argv) > 0:
            raise gdb.GdbError('This cmd DO NOT need arg.')
        Art_Global.print_dex_caches()

ArtDumpDexCaches()

class ArtDumpGlobalReference(gdb.Command):
    """
        dump gloabl reference table entries.
    """
    def __init__(self):
        super(self.__class__, self).__init__("art_dump_global_reference_table", gdb.COMMAND_USER)

    def invoke(self, args, from_tty):
        if CHECK_ANDROID_VERSION() == False:
            return
        argv = gdb.string_to_argv(args)
        if len(argv) > 0:
            raise gdb.GdbError('This cmd DO NOT need arg.')
        Art_Global.dump_global_reference_table()

ArtDumpGlobalReference()

class ArtDumpWeakGlobalReference(gdb.Command):
    """
        dump weak gloabl reference table entries.
    """
    def __init__(self):
        super(self.__class__, self).__init__("art_dump_weak_global_reference_table", gdb.COMMAND_USER)

    def invoke(self, args, from_tty):
        if CHECK_ANDROID_VERSION() == False:
            return
        argv = gdb.string_to_argv(args)
        if len(argv) > 0:
            raise gdb.GdbError('This cmd DO NOT need arg.')
        Art_Global.dump_weak_global_reference_table()

ArtDumpWeakGlobalReference()
