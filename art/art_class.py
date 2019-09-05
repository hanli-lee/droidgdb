#!/usr/bin/python                                                                                                                                                                       
# -*- coding: utf-8 -*- 
# author: hanli

import os
import sys
import gdb
import commands
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from android_runtime import AndroidRuntime


class Art_Class:
    def __init__(self, addr=0):
        self.__addr = addr
        self.__version = int(AndroidRuntime.getAndroidVersion())
        self.__name = None

    def get_name(self, needType=False):

        if self.__name != None:
            return self.__name

        class_expr = "(size_t)(('art::mirror::Class'*)%s)->name_.reference_" % self.__addr
        if self.__version == 9:
            class_expr = "(size_t)(('art::mirror::Class'*)%s)->name_.reference_.__a_" % self.__addr
            
        class_name_value = long(gdb.parse_and_eval(class_expr))
        if class_name_value != 0:
            class_str = gdb.parse_and_eval("(size_t)(('art::mirror::String' *)%s)->value_" % class_name_value)
            class_str_count = gdb.parse_and_eval("(size_t)(('art::mirror::String' *)%s)->count_" % class_name_value)
            self.__name = self.read_bytes_to_str(long(class_str), int(class_str_count))
        else:
#            print "class_name_value == 0, read descriptor from dexfile."
            dex_file_expr = "((size_t)(('art::mirror::DexCache' *)((('art::mirror::Class'*)%s)->dex_cache_.reference_))->dex_file_)" % self.__addr
                
            try:
                dex_file = gdb.parse_and_eval(dex_file_expr)
            except gdb.MemoryError:
                self.__name = "AN ARRAY CLASSS: %s " % self.__addr
                return self.__name

            dex_type_idx = gdb.parse_and_eval("(size_t)((('art::mirror::Class'*)%s)->dex_type_idx_)" % self.__addr)
            
            descriptor_idx_expr = "INVALID-DESCRIPTOR-EXPR"
            if self.__version == 8 or self.__version == 9: # verified
                descriptor_idx_expr = "((size_t)((('art::DexFile' *)%s)->type_ids_ + %s)->descriptor_idx_.index_)" % (dex_file, dex_type_idx)
            elif self.__version == 6 or self.__version == 7: # verified
                descriptor_idx_expr = "((size_t)((('art::DexFile' *)%s)->type_ids_ + %s)->descriptor_idx_)" % (dex_file, dex_type_idx)
            try:
                descriptor_idx = gdb.parse_and_eval(descriptor_idx_expr)
            except gdb.MemoryError:
                self.__name = "THE DEX FILE OF THIS CLASS NOT IN MEMORY: %s" % self.__addr
                return self.__name

            class_name_expr = "(size_t)((('art::DexFile' *)%s)->string_ids_[%s].string_data_off_ + (('art::DexFile' *)%s)->begin_ + 1)" % (dex_file, descriptor_idx, dex_file)
            if self.__version == 9:
                class_name_expr = "(size_t)((('art::DexFile' *)%s)->string_ids_[%s].string_data_off_ + (('art::DexFile' *)%s)->data_begin_ + 1)" % (dex_file, descriptor_idx, dex_file)
            class_str2 = gdb.parse_and_eval(class_name_expr)

            self.__name = self.read_bytes_to_str(long(class_str2), int(0))

        return self.__name


    def get_dex_file(self):
        dex_file_expr = "((size_t)(('art::mirror::DexCache' *)((('art::mirror::Class'*)%s)->dex_cache_.reference_))->dex_file_)" % self.__addr
        try:
            dex_file = gdb.parse_and_eval(dex_file_expr)
        except gdb.MemoryError:
            self.__name = "AN ARRAY CLASSS: %s have no dexfie" % self.__addr
            return str(0)
        return dex_file

    def get_dex_location(self):
        if self.__version == 6 or self.__version == 7 or self.__version == 8:
            dex_location_expr = "(size_t)(('art::mirror::DexCache' *)((('art::mirror::Class'*)%s)->dex_cache_.reference_))->location_.reference_" % self.__addr
        elif self.__version == 9:
            dex_location_expr = "(size_t)(('art::mirror::DexCache' *)((('art::mirror::Class'*)%s)->dex_cache_.reference_))->location_.reference_.__a_" % self.__addr

        try:
            dex_location = gdb.parse_and_eval(dex_location_expr)
        except gdb.MemoryError:
            return "AN ARRAY CLASSS: %s have no dex file" % self.__addr
        location_str_addr = long(gdb.parse_and_eval("(size_t)(('art::mirror::String'*)%s)->value_" % dex_location))
        location_str_cunt = long(gdb.parse_and_eval("(size_t)(('art::mirror::String'*)%s)->count_" % dex_location))
        location_str = self.read_bytes_to_str(location_str_addr, location_str_cunt)

        return location_str

        


    def print_name(self):
        print self.get_name()

    def print_super(self):
        print ""

    def print_summary(self):
        print "summary"
        print self.__addr;

    def print_iftable(self):
        print "interface table"

    def print_vtable(self):
        print "vtable"

    def print_methods(self):
        print "class methods"

    def print_imt(self):
        """print class interface method table"""
        print "imt: interface method table"

    def read_bytes_to_str(self, addr, size):
        result = str("")
        proc = gdb.selected_inferior()
        mem = proc.read_memory(addr, 1)
        if mem[0] == 'L': # name in dex file, verified on 6.0 / 7.0 / 8.0
            addr = addr + 1
            mem = proc.read_memory(addr, 1)

            while mem[0] != ';':
                if mem[0] == '\0':
                    print "art_class.py: zero breaked."
                    break
                if mem[0] == '/':
                    result = result + str(".")
                else:
                    result = result + chr(ord(mem[0]))
                addr = addr + 1
                mem = proc.read_memory(addr, 1)

            return result
        else:
            if self.__version == 6 or self.__version == 7: # verified
                for i in range(int(size)*2):
                    if i % 2 == 0:
                        mem = proc.read_memory(addr+i, 1)
                        if mem[0] != '0':
                            result = result + chr(ord(mem[0]))
                return result
            elif self.__version == 8 or self.__version == 9: # verified
                size = size / 2
                mem = proc.read_memory(addr, size)
                for idx in range(len(mem)):
                    if ord(mem[idx]) != 0:
                        result = result + chr(ord(mem[idx]))
                    else:
                        break
                return result

    
