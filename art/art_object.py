#!/usr/bin/python                                                                                                                                                                       
# -*- coding: utf-8 -*- 
# author: hanli

import os
import sys
import gdb
import commands
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from android_runtime import AndroidRuntime
from art_class import Art_Class

class Art_Object:
    def __init__(self, addr=0):
        self.__addr = addr
        self.__version = int(AndroidRuntime.getAndroidVersion())

        if self.__version == 9:
            class_addr_expr = "(size_t)(('art::mirror::Object'*)%s)->klass_.reference_.__a_" % self.__addr
        elif self.__version == 6 or self.__version == 7 or self.__version == 8:
            class_addr_expr = "(size_t)(('art::mirror::Object'*)%s)->klass_.reference_" % self.__addr

        self.__class_addr = gdb.parse_and_eval(class_addr_expr)
        self.__class = Art_Class(self.__class_addr)

    def get_detail_class_name(self):
        return "(art::mirror::Class *) %s  %s  %s" % (self.__class_addr, self.__class.get_name(), self.__class.get_dex_location())
        
    def get_class_name(self):
        return self.__class.get_name()

