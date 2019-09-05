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

def read_string(addr):
    result = str("")
    version = int(AndroidRuntime.getAndroidVersion())
    proc = gdb.selected_inferior()
    mem = proc.read_memory(addr, 1)
    while True:
        if mem[0] == '\0':
            break
        else:
            result = result + chr(ord(mem[0]))
        addr = addr + 1
        mem = proc.read_memory(addr, 1)
    return result

class Art_Method:
    def __init__(self, addr=0):
        self.__addr = addr

        self.__version = int(AndroidRuntime.getAndroidVersion())
        method_class_expr = "INVALID-METHOD-CLASS-EXPR"
        if self.__version == 6 or self.__version == 7 or self.__version == 8 or self.__version == 9:
            method_class_expr = "(size_t)(('art::ArtMethod'*)%s)->declaring_class_.root_.reference_" % self.__addr
        method_class = gdb.parse_and_eval(method_class_expr)

        self.__art_class = Art_Class(method_class)

        dex_method_idx = gdb.parse_and_eval("(size_t)(('art::ArtMethod'*)%s)->dex_method_index_" % self.__addr)
        if dex_method_idx == 4294967295:
            self.__name = "RuntimeMethod"
            self.__full_name = "RuntimeMethod"
            self.__paramter = ""
            self.__return_type = ""

        method_idx = gdb.parse_and_eval("(size_t)(('art::ArtMethod'*)%s)->method_index_" % self.__addr)

        dex_file = self.__art_class.get_dex_file()
#        print "dex_file: " + str(dex_file) + " , version: " + str(self.__version)
        if self.__version == 6 or self.__version == 7:
            method_name_idx_expr = "(size_t)(('art::DexFile' *)%s)->method_ids_[%s]->name_idx_" % (dex_file, dex_method_idx)
        elif self.__version == 8:
            method_name_idx_expr = "(size_t)(('art::DexFile' *)%s)->method_ids_[%s]->name_idx_.index_" % (dex_file, dex_method_idx)
        elif self.__version == 9:
            method_name_idx_expr = "(size_t)(('art::DexFile' *)%s)->method_ids_[%s]->name_idx_.index_" % (dex_file, dex_method_idx)
        method_name_idx = gdb.parse_and_eval(method_name_idx_expr)

        method_name_expr = "(size_t)((('art::DexFile' *)%s)->string_ids_[%s].string_data_off_ + (('art::DexFile' *)%s)->begin_ + 1)" % (dex_file, method_name_idx, dex_file)
        if self.__version == 9:
            method_name_expr = "(size_t)((('art::DexFile' *)%s)->string_ids_[%s].string_data_off_ + (('art::DexFile' *)%s)->data_begin_ + 1)" % (dex_file, method_name_idx, dex_file)
        method_name_value = gdb.parse_and_eval(method_name_expr)

        self.__name = read_string(long(method_name_value))
#        print "name : " + self.__name
        self.__full_name = self.__art_class.get_name() + "." + self.__name

#        print "full name: " + self.__full_name
        self.__paramter = "("
        protoid_expr = "(size_t)((('art::DexFile' *)%s)->proto_ids_ + (('art::DexFile' *)%s)->method_ids_[%s]->proto_idx_)" % (dex_file, dex_file, dex_method_idx)
        protoid = gdb.parse_and_eval(protoid_expr)
        protoid_param_off = gdb.parse_and_eval("(size_t)(('art::DexFile::ProtoId' *)%s)->parameters_off_" % protoid)
        if protoid_param_off != 0:
            type_list_expr = "(size_t)((('art::DexFile' *)%s)->begin_ + %s)" % (dex_file, protoid_param_off)
            if self.__version == 9:
                type_list_expr = "(size_t)((('art::DexFile' *)%s)->data_begin_ + %s)" % (dex_file, protoid_param_off)
            type_list = gdb.parse_and_eval(type_list_expr)
            type_list_size = gdb.parse_and_eval("(size_t)(('art::DexFile::TypeList' *)%s)->size_" % type_list)
            type_items = gdb.parse_and_eval("(size_t)(('art::DexFile::TypeList' *)%s)->list_" % type_list)
            index = int(0)
            while index < int(type_list_size):
                if self.__version == 6 or self.__version == 7:
                    descriptor_idx_expr = "(size_t)((('art::DexFile' *)%s)->type_ids_ + *((unsigned short *)%s + %s))->descriptor_idx_" % (dex_file, type_items, index)
                elif self.__version == 8 or self.__version == 9:
                    descriptor_idx_expr = "(size_t)((('art::DexFile' *)%s)->type_ids_ + *((unsigned short *)%s + %s))->descriptor_idx_.index_" % (dex_file, type_items, index)
                descritptor_idx = gdb.parse_and_eval(descriptor_idx_expr)
                param_str_expr = "(size_t)((('art::DexFile' *)%s)->string_ids_[%s].string_data_off_ + (('art::DexFile' *)%s)->begin_ + 1)" % (dex_file, descritptor_idx, dex_file)
                if self.__version == 9:
                    param_str_expr = "(size_t)((('art::DexFile' *)%s)->string_ids_[%s].string_data_off_ + (('art::DexFile' *)%s)->data_begin_ + 1)" % (dex_file, descritptor_idx, dex_file)
                param_str_value = gdb.parse_and_eval(param_str_expr)
                self.__paramter = self.__paramter + read_string(long(param_str_value))
                index = index + 1
        self.__paramter = self.__paramter + ")"
#        print "prarma: " + self.__paramter

        if self.__version == 6 or self.__version == 7:
            return_dcrptr_expr = "(size_t)((('art::DexFile' *)%s)->type_ids_ + (('art::DexFile::ProtoId' *)%s)->return_type_idx_)->descriptor_idx_" % (dex_file, protoid)
        elif self.__version == 8 or self.__version == 9:
            return_dcrptr_expr = "(size_t)((('art::DexFile' *)%s)->type_ids_ + (('art::DexFile::ProtoId' *)%s)->return_type_idx_.index_)->descriptor_idx_.index_" % (dex_file, protoid)
        return_descriptor_idx = gdb.parse_and_eval(return_dcrptr_expr)

        return_str_expr = "((size_t)(('art::DexFile' *)%s)->string_ids_[%s].string_data_off_ + (('art::DexFile' *)%s)->begin_ + 1)" % (dex_file, return_descriptor_idx, dex_file)
        if self.__version == 9:
            return_str_expr = "((size_t)(('art::DexFile' *)%s)->string_ids_[%s].string_data_off_ + (('art::DexFile' *)%s)->data_begin_ + 1)" % (dex_file, return_descriptor_idx, dex_file)
        return_str_value = gdb.parse_and_eval(return_str_expr)

        self.__return_type = read_string(long(return_str_value))
#        print "return type: " + self.__return_type
                
    def get_name(self):
        return self.__name

    def get_full_name(self):
        return self.__full_name

    def print_name(self):
        print self.__return_type + " " + self.get_full_name() + self.__paramter

