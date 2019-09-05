#!/usr/bin/python                                                                                                                                                                       
# -*- coding: utf-8 -*- 
# author: hanli

import os
import sys
import gdb
import commands
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from android_runtime import AndroidRuntime

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


class Art_Thread:
    def __init__(self, addr=0):
        self.__addr = addr
        self.__version = int(AndroidRuntime.getAndroidVersion())
        self.__lock_info = ""

    def get_state(self):
        if self.__version == 9:
            kWaitingForTaskProcessor = int(gdb.parse_and_eval("(int)'art::kWaitingForTaskProcessor'"))
        else:
            kWaitingForTaskProcessor = -1
        if self.__version == 6:
            kWaitingWeakGcRootRead = -2
            kWaitingForGcThreadFlip = -3
        else:
            kWaitingWeakGcRootRead = int(gdb.parse_and_eval("(int)'art::kWaitingWeakGcRootRead'"))
            kWaitingForGcThreadFlip = int(gdb.parse_and_eval("(int)'art::kWaitingForGcThreadFlip'"))

        status = {
            int(0) : "Unkonwn",
            int(gdb.parse_and_eval("(int)'art::kTerminated'")) : "Terminated",
            int(gdb.parse_and_eval("(int)'art::kRunnable'")) : "Runnable",
            int(gdb.parse_and_eval("(int)'art::kTimedWaiting'")) : "TimedWaiting",
            int(gdb.parse_and_eval("(int)'art::kSleeping'")) : "Sleeping",
            int(gdb.parse_and_eval("(int)'art::kBlocked'")) : "Blocked",
            int(gdb.parse_and_eval("(int)'art::kWaiting'")) : "Waiting",
            int(gdb.parse_and_eval("(int)'art::kWaitingForGcToComplete'")) : "WaitingForGcToComplete",
            int(gdb.parse_and_eval("(int)'art::kWaitingForCheckPointsToRun'")) : "WaitingForCheckPointsToRun",
            int(gdb.parse_and_eval("(int)'art::kWaitingPerformingGc'")) : "WaitingPerformingGc",
            int(gdb.parse_and_eval("(int)'art::kWaitingForDebuggerSend'")) : "WaitingForDebuggerSend",
            int(gdb.parse_and_eval("(int)'art::kWaitingForDebuggerToAttach'")) : "WaitingForDebuggerToAttach",
            int(gdb.parse_and_eval("(int)'art::kWaitingInMainDebuggerLoop'")) : "WaitingInMainDebuggerLoop",
            int(gdb.parse_and_eval("(int)'art::kWaitingForDebuggerSuspension'")) : "WaitingForDebuggerSuspension",
            int(gdb.parse_and_eval("(int)'art::kWaitingForJniOnLoad'")) : "WaitingForJniOnLoad",
            int(gdb.parse_and_eval("(int)'art::kWaitingForSignalCatcherOutput'")) : "WaitingForSignalCatcherOutput",
            int(gdb.parse_and_eval("(int)'art::kWaitingInMainSignalCatcherLoop'")) : "WaitingInMainSignalCatcherLoop",
            int(gdb.parse_and_eval("(int)'art::kWaitingForDeoptimization'")) : "WaitingForDeoptimization",
            int(gdb.parse_and_eval("(int)'art::kWaitingForMethodTracingStart'")) : "WaitingForMethodTracingStart",
            int(gdb.parse_and_eval("(int)'art::kWaitingForVisitObjects'")) : "WaitingForVisitObjects",
            int(gdb.parse_and_eval("(int)'art::kWaitingForGetObjectsAllocated'")) : "WaitingForGetObjectsAllocated",
            kWaitingWeakGcRootRead : "WaitingWeakGcRootRead",
            kWaitingForGcThreadFlip : "WaitingForGcThreadFlip",
            int(gdb.parse_and_eval("(int)'art::kStarting'")) : "Starting",
            int(gdb.parse_and_eval("(int)'art::kNative'")) : "Native",
            int(gdb.parse_and_eval("(int)'art::kSuspended'")) : "Suspended",
            kWaitingForTaskProcessor : "WaitingForTaskProcessor"
        }
        state = gdb.parse_and_eval("(int)(('art::Thread'*)%s)->tls32_->state_and_flags.as_struct.state" % self.__addr)
        internal_state = ""
        owner_tid = -1
        if int(state) == int(gdb.parse_and_eval("(int)'art::kBlocked'")):
            lock_object = int(gdb.parse_and_eval("(size_t)(('art::Thread'*)%s)->tlsPtr_.monitor_enter_object" % self.__addr))
            if lock_object != 0:
                monitor_addr = int(lock_object) + 4
                state_shift = int(gdb.parse_and_eval("(int)'art::LockWord::SizeShiftsAndMasks::kStateShift'"))
                state_mask  = int(gdb.parse_and_eval("(int)'art::LockWord::SizeShiftsAndMasks::kStateMask'"))
#                print "hanli: " + str(state_shift) + ", " + str(state_mask)
                lock_state = int(gdb.parse_and_eval("(((uint32_t)(*((uint32_t*)%s))) >> %s) & %s" % (monitor_addr, state_shift, state_mask)))
                state_thin_or_unlocked = int(gdb.parse_and_eval("'art::LockWord::SizeShiftsAndMasks::kStateThinOrUnlocked'"))
                state_hash = int(gdb.parse_and_eval("'art::LockWord::SizeShiftsAndMasks::kStateHash'"))
                state_forwarding_addr = int(gdb.parse_and_eval("'art::LockWord::SizeShiftsAndMasks::kStateForwardingAddress'"))
                state_fat_locked = int(gdb.parse_and_eval("'art::LockWord::SizeShiftsAndMasks::kStateFat'"))
                if lock_state == state_thin_or_unlocked:
                    owner_tid = 0
                    self.__lock_info = "(thin_or_lock)" + str(monitor_addr)
                elif lock_state == state_hash:
                    owner_tid = 0
                    self.__lock_info = "(state_hash)" + str(monitor_addr)
                elif lock_state == state_forwarding_addr:
                    owner_tid = 0
                    self.__lock_info = "(forward)" + str(monitor_addr)
                elif lock_state == state_fat_locked:
                    monitor_id_shift = int(gdb.parse_and_eval("(int)'art::LockWord::SizeShiftsAndMasks::kMonitorIdShift'"))
                    monitor_id_mask = int(gdb.parse_and_eval("(int)'art::LockWord::SizeShiftsAndMasks::kMonitorIdMask'"))
                    monitor_id = int(gdb.parse_and_eval("(((uint32_t)(*((uint32_t*)%s))) >> %s) & %s" % (monitor_addr, monitor_id_shift, monitor_id_mask)))
                    monitor_id_align_shift = int(gdb.parse_and_eval("(int)'art::LockWord::SizeShiftsAndMasks::kMonitorIdAlignmentShift'"))
                    void_pointer_size = int(gdb.parse_and_eval("sizeof(void*)"))
                    if void_pointer_size == 4:
                        Monitor = long(gdb.parse_and_eval("%s << %s" % (monitor_id, monitor_id_align_shift)))
                        owner_thread = long(gdb.parse_and_eval("(('art::Monitor'*)%s)->owner_" % Monitor))
                    elif void_pointer_size == 8:
                        chunk_size = int(gdb.parse_and_eval("'art::MonitorPool::kChunkSize'"))
                        max_list_size = int(gdb.parse_and_eval("'art::MonitorPool::kMaxListSize'"))
                        offset = monitor_id << 3
                        index = offset/chunk_size
                        top_index = index/max_list_size
                        list_index = index%max_list_size
                        offset_in_chunk = offset%chunk_size
                        base = long(gdb.parse_and_eval("(size_t)'art::Runtime'::instance_->monitor_pool_->monitor_chunks_[%s][%s]" % (top_index, list_index)))
                        addr = base + offset_in_chunk
                        owner_thread = long(gdb.parse_and_eval("(size_t)((('art::Monitor'*)%s)->owner_)" % addr))
                    owner_tid = int(gdb.parse_and_eval("(('art::Thread'*)%s)->tls32_.tid" % owner_thread))
                    self.__lock_info = " (waitting to lock " + str(hex(lock_object)) + " held by " + str(owner_tid) + ")"
        return status.get(int(state), None)

    def get_lock_info(self):
        return self.__lock_info

    def get_mutex(self):
        lock_level_count  = gdb.parse_and_eval("(int)'art::kLockLevelCount'")
        index = int(0)
        result = ""
        while index < int(lock_level_count):
            base_mutex = gdb.parse_and_eval("(size_t)(('art::Thread'*)%s)->tlsPtr_.held_mutexes[%s]" % (self.__addr, index))
            if long(base_mutex) != 0:
                if self.__version == 6 or self.__version == 7 or self.__version == 8:
                    name_expr = "(size_t)(('art::Thread'*)%s)->tlsPtr_.held_mutexes[%s]->name_" % (self.__addr, index)
                elif self.__version == 9:
                    name_expr = "(size_t)(('art::Thread'*)%s)->tlsPtr_.held_mutexes[%s]->name_" % (self.__addr, index)
                name_addr = gdb.parse_and_eval(name_expr)
                result = result + read_string(long(name_addr)) + "(" + str(index) + ")"
#                is_read_write_mutex = (int(gdb.parse_and_eval("(('art::BaseMutex'*)%s)->IsReaderWriterMutex()" % base_mutex)) != 0)
                if self.is_readwrite_mutex(index):
                    state = int(gdb.parse_and_eval("(size_t)(('art::ReaderWriterMutex'*)%s)->state_->__a_" % base_mutex))
                    if state == 0:
                        owner = 0
                    elif state > 0:
                        owner = -1
                    else:
                        owner = int(gdb.parse_and_eval("(int)(('art::ReaderWriterMutex'*)%s)->exclusive_owner_" % base_mutex))

                    if owner  == int(gdb.parse_and_eval("(int)(('art::Thread'*)%s)->tls32_->tid" % self.__addr)):
                        result = result + "(exclusive held)"
                    else:
                        result = result + "(shared held)(owner: %s)" % str(owner)
            index = index + 1

        return result

    def is_readwrite_mutex(self, lock_level):

        if self.__version == 8 or self.__version == 9:
            kVerifierDepsLock = int(gdb.parse_and_eval("(int)'art::kVerifierDepsLock'"))
            kDexLock = int(gdb.parse_and_eval("(int)'art::kDexLock'"))
        else:
            kVerifierDepsLock = -1
            kDexLock = -2

        if self.__version == 6:
            kJniGlobalsLock = -3
            kOatFileManagerLock = -4
            kDeoptimizedMethodsLock = -5
            kClassLoaderClassesLock = -6
        else:
            kJniGlobalsLock = int(gdb.parse_and_eval("(int)'art::kJniGlobalsLock'"))
            kOatFileManagerLock = int(gdb.parse_and_eval("(int)'art::kOatFileManagerLock'"))
            kDeoptimizedMethodsLock = int(gdb.parse_and_eval("(int)'art::kDeoptimizedMethodsLock'"))
            kClassLoaderClassesLock = int(gdb.parse_and_eval("(int)'art::kClassLoaderClassesLock'"))

        readwrite_mutex_lock_level = {
            int(gdb.parse_and_eval("(int)'art::kRosAllocBulkFreeLock'")) : True,
            kJniGlobalsLock : True,
            kVerifierDepsLock : True,
            kOatFileManagerLock : True,
            kDeoptimizedMethodsLock : True,
            kClassLoaderClassesLock : True,
            kDexLock : True,
            int(gdb.parse_and_eval("(int)'art::kClassLinkerClassesLock'")) : True,
            int(gdb.parse_and_eval("(int)'art::kBreakpointLock'")) : True,
            int(gdb.parse_and_eval("(int)'art::kHeapBitmapLock'")) : True,
            int(gdb.parse_and_eval("(int)'art::kMutatorLock'")) : True,
        }

        return readwrite_mutex_lock_level.get(lock_level, False)






