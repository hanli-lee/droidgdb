#!/usr/bin/python                                                                                                                                                                       
# -*- coding: utf-8 -*- 
# author: hanli

import os
import sys
import gdb
import commands
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from art_object import Art_Object
from art_class import Art_Class
from android_runtime import AndroidRuntime
from art_thread_list import Art_Thread_List

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

def read_android6_str_by_size(addr, size):
    result = str("")
    proc = gdb.selected_inferior()
    version = int(AndroidRuntime.getAndroidVersion())
    if version == 6 or version == 7: # verified
        for i in range(int(size)*2):
            if i % 2 == 0:
                mem = proc.read_memory(addr+i, 1)
                if mem[0] != '0':
                    result = result + chr(ord(mem[0]))
    return result



class Art_Global:
    @classmethod
    def print_dex_caches(cls):
        version = int(AndroidRuntime.getAndroidVersion())

        if version == 6:
            print "\n  Id    'art::mirror::DexCache'*   'art::DexFile'*     dex_location"
            vector_begin = long(gdb.parse_and_eval("(size_t)'art::Runtime'::instance_->class_linker_->dex_caches_->__begin_"))
            vector_end = long(gdb.parse_and_eval("(size_t)'art::Runtime'::instance_->class_linker_->dex_caches_->__end_"))
            index = vector_begin
            count = 0
            while index < vector_end:
                gc_root = long(gdb.parse_and_eval("(size_t)(*(void**)%s)" % index))
                dex_cache = long(gdb.parse_and_eval("(size_t)(('art::GcRoot<art::mirror::DexCache>')%s).root_.reference_" % gc_root))
                dex_file = long(gdb.parse_and_eval("(size_t)(('art::mirror::DexCache'*)%s)->dex_file_" % dex_cache))
                location = long(gdb.parse_and_eval("(size_t)(('art::mirror::DexCache'*)%s)->location_.reference_" % dex_cache))
                location_str_addr = long(gdb.parse_and_eval("(size_t)(('art::mirror::String'*)%s)->value_" % location))
                location_str_cunt = long(gdb.parse_and_eval("(size_t)(('art::mirror::String'*)%s)->count_" % location))
                location_str = read_android6_str_by_size(location_str_addr, location_str_cunt)
                print "  %2d  %20s  %20s      %s" % (count, hex(dex_cache), hex(dex_file), location_str)
                index = long(gdb.parse_and_eval("(size_t)(((void**)%s) +1)" % index))
                count  = count + 1
            print ""
            return

        list_node_expr = "(size_t)'art::Runtime'::instance_->class_linker_->dex_caches_->__end_->__next_"
        if version == 7:
            size_expr = "(size_t)'art::Runtime'::instance_->class_linker_->dex_caches_->__size_alloc_->__first_"
            print "\n  Id  DexCacheData*    DexCache*   GcRoot<mirror::Class>*   'art::DexFile'*     dex_location"
#                                  p (('art::GcRoot<art::mirror::Class>'*)0x70cac518L)[5]
        elif version == 8:
            size_expr = "(size_t)'art::Runtime'::instance_->class_linker_->dex_caches_->__size_alloc_->__first_"
            print "\n  Id  DexCacheData*    DexCache*   'art::ArtMethod'**   'art::ClassTable'*   'art::DexFile'*     dex_location"
        elif version == 9:
            size_expr = "(size_t)'art::Runtime'::instance_->class_linker_->dex_caches_->__size_alloc_->__value_"
            print "\n  Id  DexCacheData*    DexCache*   'art::ClassTable'*   'art::DexFile'*     dex_location"

        list_node = gdb.parse_and_eval(list_node_expr)
#        gdb.execute("p 'art::Runtime'::instance_->class_linker_->dex_caches_->__end_->__next_")
        size = gdb.parse_and_eval(size_expr)
        index = 0
        while index < size:
            if version == 7 and index == 0:
                dex_cache_data = long(gdb.parse_and_eval("(size_t)(&'art::Runtime'::instance_->class_linker_->dex_caches_->__end_->__next_->__value_)"))
                weak_root = gdb.parse_and_eval("(size_t)('art::Runtime'::instance_->class_linker_->dex_caches_->__end_->__next_->__value_->weak_root)")
                dex_file = hex(long(gdb.parse_and_eval("(size_t)('art::Runtime'::instance_->class_linker_->dex_caches_->__end_->__next_->__value_->dex_file)")))
            else:
                dex_cache_data = long(gdb.parse_and_eval("((size_t)%s + 2*sizeof(void*))" % list_node))
                weak_root = gdb.parse_and_eval("(size_t)(('art::ClassLinker::DexCacheData' *)%s)->weak_root" % dex_cache_data)
                dex_file = hex(long(gdb.parse_and_eval("(size_t)(('art::ClassLinker::DexCacheData'*)%s)->dex_file" % dex_cache_data)))
                
            dex_cache_data = hex(dex_cache_data)
            art_thread_list = Art_Thread_List()
            dex_cache = art_thread_list.decode_jobject(weak_root)
            if version == 7:
                location_addr_expr = "(size_t)(('art::DexFile'*)%s)->location_->__r_->__first_->__r->__words[2]" % dex_file
                location_size_expr = "(size_t)(('art::DexFile'*)%s)->location_->__r_->__first_->__r->__words[1]" % dex_file
                next_expr = "(size_t)(('std::__1::__list_node_base<art::ClassLinker::DexCacheData, void*>::pointer')%s)->__next_" % list_node
                resolved_methods = hex(long(gdb.parse_and_eval("(size_t)(('art::ClassLinker::DexCacheData'*)%s)->resolved_types" % dex_cache_data)))
            elif version == 8:
                location_addr_expr = "(size_t)(('art::DexFile'*)%s)->location_->__r_->__first_->__r->__words[2]" % dex_file
                location_size_expr = "(size_t)(('art::DexFile'*)%s)->location_->__r_->__first_->__r->__words[1]" % dex_file
                next_expr = "(size_t)(('std::__1::__list_node_base<art::ClassLinker::DexCacheData, void*>::__link_pointer')%s)->__next_" % list_node
                resolved_methods = hex(long(gdb.parse_and_eval("(size_t)(('art::ClassLinker::DexCacheData'*)%s)->resolved_methods" % dex_cache_data)))
                class_table = hex(long(gdb.parse_and_eval("(size_t)(('art::ClassLinker::DexCacheData'*)%s)->class_table" % dex_cache_data)))
            elif version == 9:
                location_addr_expr = "(size_t)(('art::DexFile'*)%s)->location_->__r_->__value_->__r->__words[2]" % dex_file
                location_size_expr = "(int)(('art::DexFile'*)%s)->location_->__r_->__value_->__r->__words[1]" % dex_file
                next_expr = "(size_t)(('std::__1::__list_node_base<art::ClassLinker::DexCacheData, void*>::__link_pointer')%s)->__next_" % list_node
                class_table = hex(long(gdb.parse_and_eval("(size_t)(('art::ClassLinker::DexCacheData'*)%s)->class_table" % dex_cache_data)))
            dex_location_addr = gdb.parse_and_eval(location_addr_expr)
            dex_location_size = gdb.parse_and_eval(location_size_expr)
            dex_location = read_string_by_size(long(dex_location_addr), int(dex_location_size))

            if dex_cache == None:
                dex_cache = hex(long(0))
            else:
                dex_cache = hex(long(dex_cache))

            if version == 7:
                print "  %2d  %12s  %12s  %16s  %21s      %s" % (index, dex_cache_data, dex_cache, resolved_methods, dex_file, dex_location)
            elif version == 8:
                print "  %2d  %12s  %12s  %15s  %20s  %17s      %s" % (index, dex_cache_data, dex_cache, resolved_methods, class_table, dex_file, dex_location)
            elif version == 9:
                print "  %2d  %12s  %12s  %15s  %18s      %s" % (index, dex_cache_data, dex_cache, class_table, dex_file, dex_location)
            list_node = gdb.parse_and_eval(next_expr)
            index = index + 1
        print ""

    @classmethod
    def dump_indirect_reference_table(cls, table):
        version = int(AndroidRuntime.getAndroidVersion())
        if version == 9 or version == 8:
            kind_expr = "(('art::IndirectReferenceTable' *)%s)->kind_" % table
            max_index_expr = "(size_t)(('art::IndirectReferenceTable' *)%s)->segment_state_.top_index" % table
        else:
            kind_expr = "(('art::IndirectReferenceTable' *)%s)->kind_" % table
            max_index_expr = "(size_t)(('art::IndirectReferenceTable' *)%s)->segment_state_->parts->topIndex" % table
        max_entries_expr = "(size_t)(('art::IndirectReferenceTable' *)%s)->max_entries_" % table
        irt_entry_table_expr = "(size_t)(('art::IndirectReferenceTable' *)%s)->table_" % table
        
        kind = gdb.parse_and_eval(kind_expr)
        max_index = gdb.parse_and_eval(max_index_expr)
        max_entries = gdb.parse_and_eval(max_entries_expr)
        irt_entry_table = gdb.parse_and_eval(irt_entry_table_expr)

        print "\n%s reference table dump(%s):\n" % (kind, max_index)
        print "  Index     object"
        index = 0
        while index < max_index:
            irt_entry_expr = "(size_t)(&(('art::IndirectReferenceTable' *)%s)->table_[%s])" % (table, index)
            irt_entry = gdb.parse_and_eval(irt_entry_expr)
            serial = gdb.parse_and_eval("(size_t)(('art::IrtEntry'*)%s)->serial_" % irt_entry)
            real_object = gdb.parse_and_eval("(size_t)(('art::IrtEntry'*)%s)->references_[%s]->root_->reference_" % (irt_entry, serial))

            if long(real_object) > 0:
                try:
                    art_object = Art_Object(real_object)
                    object_class_name = art_object.get_class_name()
                except gdb.MemoryError:
                    print "art_global.object: %s" % real_object
                    break
                if object_class_name == "java.lang.ref.WeakReference":
                    print "get referent class name"
                elif object_class_name == "java.lang.Class":
                    art_class = Art_Class(real_object)
                    print "%5s :     java.lang.Class(%s)" % (index, art_class.get_name())
                else:
                    print "%5s :     %s" % (index, object_class_name)
                    
            else:
                print "%5s :     ***********hole[%s]************" % (index, index)
            index = index + 1
                

    @classmethod
    def dump_global_reference_table(cls):
        version = int(AndroidRuntime.getAndroidVersion())
        if version == 6 or version == 7:
            table_expr = "(size_t)(&('art::Runtime'::instance_->java_vm_->globals_))"
        elif version == 8:
            table_expr = "(size_t)(&('art::Runtime'::instance_->java_vm_.__ptr_.__first_->globals_))"
        elif version == 9:
            table_expr = "(size_t)(&('art::Runtime'::instance_->java_vm_.__ptr_.__value_->globals_))"

        global_reference_table = gdb.parse_and_eval(table_expr)
        Art_Global.dump_indirect_reference_table(global_reference_table)


    @classmethod
    def dump_weak_global_reference_table(cls):
        version = int(AndroidRuntime.getAndroidVersion())
        if version == 6 or version == 7:
            table_expr = "(size_t)(&('art::Runtime'::instance_->java_vm_->weak_globals_))"
        elif version == 8:
            table_expr = "(size_t)(&('art::Runtime'::instance_->java_vm_.__ptr_.__first_->weak_globals_))"
        elif version == 9:
            table_expr = "(size_t)(&('art::Runtime'::instance_->java_vm_.__ptr_.__value_->weak_globals_))"

        weak_global_reference_table = gdb.parse_and_eval(table_expr)
        Art_Global.dump_indirect_reference_table(weak_global_reference_table)









