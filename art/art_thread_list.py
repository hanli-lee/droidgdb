#!/usr/bin/python                                                                                                                                                                       
# -*- coding: utf-8 -*- 
# author: hanli

import os
import sys
import gdb
import commands
import exceptions
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from android_runtime import AndroidRuntime
from art_thread import Art_Thread

def read_string_by_size(addr, size):
    result = str("")
    proc = gdb.selected_inferior()
    mem = proc.read_memory(addr, size)
    for idx in range(len(mem)):
        if ord(mem[idx]) != 0:
            result = result + chr(ord(mem[idx]))
        else:
            break

    return result

def read_string(addr):
    result = str("")
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

class Art_Thread_List:
    def __init__(self):
        self.__version = int(AndroidRuntime.getAndroidVersion())

    def decode_jobject(self, jobject, thread = 0):
        if str(jobject).startswith('0x'):
            ref_kind = int(long(jobject, 16) & 0x3)
            ref_idx = int((long(jobject, 16) >> 2) & 0xffff)
        else:
            ref_kind = int(long(jobject) & 0x3)
            ref_idx = int((long(jobject) >> 2) & 0xffff)

#        print "ref_kind: " + str(ref_kind) + " ,ref_idx: " + str(ref_idx)


        if ref_kind == 0:
            decoded_obj = gdb.parse_and_eval("(size_t)(('art::StackReference<art::mirror::Object>'*)%s)->reference_" % jobject)
            return str(decoded_obj)

        if ref_kind == 1:
#            print " kLocal "
            if thread > 0:
                if self.__version == 6 or self.__version == 7 or self.__version == 8:
                    IrtEntry = gdb.parse_and_eval("(size_t)(&((('art::Thread'*)%s)->tlsPtr_.jni_env->locals->table_[%s]))" % (thread, ref_idx))
                elif self.__version == 9:
                    IrtEntry = gdb.parse_and_eval("(size_t)(&((('art::Thread'*)%s)->tlsPtr_.jni_env->locals_->table_[%s]))" % (thread, ref_idx))
            else:
                raise gdb.GdbError('ERROR, decoding a thread local reference need a thread pointer.')
        elif ref_kind == 2:
#            print " kGlobal "
            if self.__version == 6 or self.__version == 7:
                irt_entry_expr = "(size_t)(&('art::Runtime'::instance_->java_vm_->globals_->table_[%s]))" % ref_idx
            elif self.__version == 8:
                irt_entry_expr = "(size_t)(&('art::Runtime'::instance_->java_vm_.__ptr_.__first_->globals_->table_[%s]))" % ref_idx
            elif self.__version == 9:
                irt_entry_expr = "(size_t)(&('art::Runtime'::instance_->java_vm_.__ptr_.__value_->globals_->table_[%s]))" % ref_idx
            IrtEntry = gdb.parse_and_eval(irt_entry_expr)

        elif ref_kind == 3:
#            print " kWeakGlobal "
            if self.__version == 6 or self.__version == 7:
                irt_entry_expr = "(size_t)(&('art::Runtime'::instance_->java_vm_->weak_globals_->table_[%s]))" % ref_idx
            elif self.__version == 8:
                irt_entry_expr = "(size_t)(&('art::Runtime'::instance_->java_vm_.__ptr_.__first_->weak_globals_->table_[%s]))" % ref_idx
            elif self.__version == 9:
                irt_entry_expr = "(size_t)(&('art::Runtime'::instance_->java_vm_.__ptr_.__value_->weak_globals_->table_[%s]))" % ref_idx
            IrtEntry = gdb.parse_and_eval(irt_entry_expr)

        if long(IrtEntry) > 0:
            serial = gdb.parse_and_eval("(size_t)(('art::IrtEntry'*)%s)->serial_" % IrtEntry)
            real_object = gdb.parse_and_eval("(size_t)(('art::IrtEntry'*)%s)->references_[%s]->root_->reference_" % (IrtEntry, serial))
            if long(real_object) > 0:
                return str(real_object)
            else:
                return "0"
        else:
            return "Have No IrtEntry."
        
    def dump(self, dump_mutext = False):
        if self.__version == 9:
            list_node_expr = "(size_t)('art::Runtime'::instance_)->thread_list_->list_->__end_->__next_"
            list_size_expr = "(size_t)('art::Runtime'::instance_)->thread_list_->list_->__size_alloc_->__value_"
        elif self.__version == 6 or self.__version == 7 or self.__version == 8:
            list_node_expr = "(size_t)('art::Runtime'::instance_)->thread_list_->list_->__end_->__next_"
            list_size_expr = "(size_t)('art::Runtime'::instance_)->thread_list_->list_->__size_alloc_->__first_"

        list_node = gdb.parse_and_eval(list_node_expr)
        list_size = gdb.parse_and_eval(list_size_expr)
        index = int(1)
#       print "\n Id  Tid   art::Thread*  sCount  dtfCount     STATE         NAME                                 MUTEX\n"
        print "\n%3s  %5s   %10s  %4s  %6s       %-30s      %-35s       %s"% ("Id", "Tid", "art::Thread*", "sCount", "dtfCount", "STATE", "NAME", "MUTEX")
        try:
            while int(index) <= int(list_size):
                thread_expr = "('art::Thread'*)(*(void**)((size_t)%s + 2*sizeof(void*)))" % list_node
                thread = gdb.parse_and_eval(thread_expr)
                if self.__version == 9:
                    name_expr = "(size_t)(('art::Thread'*)%s)->tlsPtr_->name->__r_->__value_->__r->__words[2]" % thread
                    size_expr = "(size_t)(('art::Thread'*)%s)->tlsPtr_->name->__r_->__value_->__r->__words[1]" % thread
                elif self.__version == 6 or self.__version == 7 or self.__version == 8:
                    name_expr = "(size_t)(('art::Thread'*)%s)->tlsPtr_->name->__r_->__first_->__r->__words[2]" % thread
                    size_expr = "(size_t)(('art::Thread'*)%s)->tlsPtr_->name->__r_->__first_->__r->__words[1]" % thread

                name_addr = gdb.parse_and_eval(name_expr)
                name_size = gdb.parse_and_eval(size_expr)

                tid = gdb.parse_and_eval("(('art::Thread'*)%s)->tls32_->tid" % thread)
                suspend_count = gdb.parse_and_eval("(('art::Thread'*)%s)->tls32_->suspend_count" % thread)
                if self.__version == 6:
                    dtfCount = -1
                else:
                    dtfCount = gdb.parse_and_eval("(('art::Thread'*)%s)->tls32_->disable_thread_flip_count" % thread)

                name = read_string_by_size(long(name_addr), long(name_size))

                art_thread = Art_Thread(thread)
                state_str = art_thread.get_state()
                if dump_mutext:
                    mutex_str = art_thread.get_mutex()
                else:
                    mutex_str = art_thread.get_lock_info()
                print "%3d  %5d   %10s  %4d  %6d        %-30s     %-35s      %s" % (index, tid, thread, suspend_count, dtfCount, state_str, name, mutex_str)


                if self.__version == 8 or self.__version == 9:
                    next_expr = "(size_t)((('std::__1::__list_node_base<art::Thread*, void*>::__link_pointer')%s)->__next_)" % list_node
                elif self.__version == 6 or self.__version == 7:
                    next_expr = "(size_t)((('std::__1::__list_node_base<art::Thread*, void*>::pointer')%s)->__next_)" % list_node
                list_node = gdb.parse_and_eval(next_expr)

                index  = index + 1
        except exceptions.KeyboardInterrupt:
            return

        print ""

