
define art_print_rosalloc_runs
    set $ros_cur_runs_ = 'art::Runtime::instance_'->heap_->rosalloc_space_->rosalloc_->current_runs_
    set $index = (int)0
    while $index < 42
        set $run = $ros_cur_runs_[$index]
        set $run_idx = $ros_cur_runs_[$index]->size_bracket_idx_
        set $head = $ros_cur_runs_[$index]->free_list_->head_
        printf "run[%d]: %p, index: %d, free_list_head: %p\n", $index, $run, $run_idx, $head
        set $index = $index + 1
    end
end

define art_print_dexfile
    set $dex_file=(const art::DexFile *)$arg0
        print "setAndroidVersoin: " + str(version)
    printf "art::DexFile *    methods_count    classes_count    location\n"
    printf " 0x%x         %05d            %05d           ", (size_t)$dex_file, $dex_file->header_->method_ids_size_, $dex_file->header_->class_defs_size_
    set $location=$dex_file->location_->__r_->__first_->__r->__words[2]
    set $count = $dex_file->location_->__r_->__first_->__r->__words[1]
    art_print_cstring $location $count
    printf "\n"
end

define art_get_dexfile
    set $dex_file=('art::DexFile' *)$arg0
    set $location=$dex_file->location_->__r_->__first_->__r->__words[2]
    set $count = $dex_file->location_->__r_->__first_->__r->__words[1]
    art_print_cstring $location $count
end

define art_print_dexcache
    set $dexcache=(art::mirror::DexCache*)$arg0
    printf "resolved_methods_= 0x%x \n", $dexcache->resolved_methods_.reference_
    art_print_dexfile (size_t)$dexcache->dex_file_
end

define art_get_dexcache
    set $dexcache = ('art::mirror::DexCache' *)$arg0
    printf "0x%x         ", (size_t)$dexcache->dex_file_
    art_get_dexfile (size_t)($dexcache->dex_file_)
end





define art_dump_class_loaders
    set $class_loaders_=('art::Runtime'::instance_)->class_linker_->class_loaders_
    set $loaders_size=('art::Runtime'::instance_)->class_linker_->class_loaders_->__size_alloc_->__first_
    p $loaders_size
    p $class_loaders_
    set $invalid=&(('art::Runtime'::instance_)->class_linker_->class_loaders_)
    set $last=('art::Runtime'::instance_)->class_linker_->class_loaders_->__end_->__prev_
    set $next=('art::Runtime'::instance_)->class_linker_->class_loaders_->__end_->__next_
    
    set $index = (int)0

    while $index <= $loaders_size
        if  $next != $invalid
            p $next
            set $weak_root=(int)$next->__value_->weak_root
            p /x $weak_root
            set $class_table=$next->__value_->class_table
            p $class_table
            set $class_set_vector_=&($class_table->classes_)
            p $class_set_vector_->__begin_
            p $class_set_vector_->__end_
        end
        set $next=$next->__next_
        set $index = $index + 1
    end

    printf "\n-------------\n"
    p $last
    p $next
end

define art_print_weak_refs
    p 'art::Runtime'::instance_->java_vm_->weak_globals_
    printf "art::Runtime::instance_->java_vm_->weak_globals_ \n"
    printf "reftable.Get(uref), index = (uref >> 2) & 0xffff;\n"
    printf "obj = table_[index] \n"
end


define art_dump_global_refs

    set $table=&('art::Runtime'::instance_)->java_vm_->globals_
    dump_IRT_table  $table
end

define art_dump_weak_global_refs

    set $table=&'art::Runtime'::instance_->java_vm_->weak_globals_
    dump_IRT_table  $table
end

define art_dump_local_refs
    set $env=$arg0
    set $table=&(('art::JNIEnvExt' * )$env)->locals
    dump_IRT_table  $table
end

define dump_IRT_table
    set $table=('art::IndirectReferenceTable' *)$arg0

    set $kind=$table->kind_
    set $max_idx=$table->segment_state_->parts->topIndex
    set $holes=$table->segment_state_->parts->numHoles
    set $max_entries_=$table->max_entries_

    if $kind == 1
        printf "local"
    end
    if $kind == 2
        printf "global"
    end
    if $kind ==3
        printf "weak global"
    end

    printf " reference table dump (top=%d holes=%d max=%d):\n",$max_idx,$holes,$max_entries_
    set $table_=$table->table_

    set $index = (int)0
    set $unkown_count= (int)0

    while $index < $max_idx
        set $serial=$table_[$index]->serial_
        set $object=$table_[$index]->references_[$serial]->root_->reference_
        if $object != 0
            p $object
            printf ""

            set $curclass = ('art::mirror::Class' *)((('art::mirror::Object' *)$object)->klass_.reference_)
            set $classstring = ('art::mirror::String' *)($curclass->name_.reference_)
            if $classstring != 0
                set $local_string = $classstring
                set $string_length  = (int) $local_string->count_
                set $declaringstr = (char*)($local_string->value_)
                set $logcal_index = (int) 0
                set $string_length = (int) 2*$string_length
                
                printf "index: %d    ",$index
                while $logcal_index < $string_length
                        printf "%c", *($declaringstr + $logcal_index)
                    set $logcal_index = $logcal_index + 2 
                end
                printf "\n"
            else
                set $unkown_count = $unkown_count + 1
            end
        else
            printf "a hole at %d\n", $index
        end

        set $index = $index + 1
    end
    printf "%d UNKOWN TYPE OBJECT\n",$unkown_count
end

define art_print_collectors
    set $collector_addr='art::Runtime'::instance_->heap_->garbage_collectors_->__begin_
    set $end = 'art::Runtime'::instance_->heap_->garbage_collectors_->__end_
    p $collector_addr
    p $end
    while $collector_addr < $end
        set $first_collector=*($collector_addr)
        if $first_collector->name_->__r_->__first_->__l->__size_ < 4096
            set $name_str=$first_collector->name_->__r_->__first_->__l->__data_
        else
            set $name_str=$first_collector->name_->__r_->__first_->__s->__data_
        end
        art_print_cstring $name_str 0
        printf "\n"
        set $collector_addr=$collector_addr+1
    end
end

define class_print_super
    printf "current[%p]: ", $arg0
    class_print_name_ $arg0
    set $myclass = ('art::mirror::Class' *)$arg0
    set $super = $myclass->super_class_.reference_
    printf "super[%p]: ",$super
    class_print_name_ $super
end

define get_class_name_base
    set $myclass = ('art::mirror::Class' *)$arg0
    
    set $show_class_type = 1
    if $arg1 == 0
        set $show_class_type = 0
    end

##    set $classstring = ('art::mirror::String' *)($myclass->name_.reference_)
##9.0
    set $classstring = ('art::mirror::String' *)($myclass->name_->reference_.__a_)

    if $classstring != 0
        set $class_str = $classstring->value_
##        art_print_cstring $class_str $classstring->count_*2
##9.0
        art_print_cstring $class_str 0
    else
        set $dexfile = ('art::DexFile' *) ((size_t)(('art::mirror::DexCache' *)$myclass->dex_cache_.reference_)->dex_file_)
        set $dextypeidx = (size_t) $myclass->dex_type_idx_
        set $descriptoridx = (size_t) ($dexfile->type_ids_ + $dextypeidx)->descriptor_idx_
        set $classnameptr = (size_t) ($dexfile->string_ids_[$descriptoridx].string_data_off_ + $dexfile->begin_ + 1)
        art_print_cstring $classnameptr 0
    end

    set $is_primitive = (size_t)0
    set $is_interface = (size_t)0
    set $is_abstract = (size_t)0
    set $is_array_class = (size_t)0

    set $kPrimitiveTypeMask = (size_t)((1 << 16) - 1)
    if ($myclass->primitive_type_ & $kPrimitiveTypeMask) != 0
        set $is_primitive = (size_t)1
        if $show_class_type != 0
            printf "   [Primitive]"
        end
    end

    set $acc_flag = $myclass->access_flags_

    if ($acc_flag & 0x0400) != 0
        set $is_abstract = (size_t)1
        if $show_class_type != 0
            printf "   [Abstract]"
        end
    end

    if ($acc_flag & 0x0200) != 0
        set $is_interface = (size_t)1
        if $show_class_type != 0
            printf "   [Interface]"
        end

    end

    if $myclass->component_type_.reference_ != 0
        set $is_array_class = (size_t)1
        if $show_class_type != 0
            printf "[Array Class]"
        end
    end


    set $is_instantiable = (int)0

    if ($is_primitive + $is_interface + $is_abstract) == 0
        set $is_instantiable = (int)1
        if $show_class_type != 0
            printf "   [Normal]"
        end
    else
        if ($is_abstract + $is_array_class) == 2
            set $is_instantiable = (int)1
        end

    end
end

define print_object_class
    set $curclass = ('art::mirror::Class' *)((('art::mirror::Object' *)$arg0)->klass_.reference_)
    p $curclass
    class_print_name_ $curclass
end

define class_print_iftable

    set $myclass = ('art::mirror::Class' *)$arg0
    printf "\nCLASS NAME:   "
    class_print_name_ $myclass
    set $iftable = ('art::mirror::IfTable' *)($myclass->iftable_.reference_)

    if $iftable != 0
        set $iftable_length = $iftable->length_
        set $first_element_ = $iftable->first_element_
    
        set $index = (int) 0

        while $index < $iftable_length
            set $ptr = $first_element_[$index]
            if $index % 2 == 0
                printf "\nInterface[%p]: ",$ptr
                class_get_name $ptr
            else
                printf "        *('art::mirror::PointerArray'*)(0x%x) \n",$ptr
                if $ptr == 0
                    printf "     This Interface have no method.\n"
                else
                    set $method_array = ('art::mirror::PointerArray'*)($ptr)
                    set $method_array_len = $method_array->length_
                    set $method_array_fist_elem = $method_array->first_element_
                    printf "     first0: %p \n",$method_array_fist_elem
                    if sizeof(void*) == 8
                        set $method_array_fist_elem = (size_t)($method_array_fist_elem)+4
                    end
                    printf "     first1: %p \n",$method_array_fist_elem
                    set $idx = (int) 0
                    while $idx < $method_array_len
                        printf "     ArtMethod[%02d][0x%010lx]: ",$idx,*((void**)($method_array_fist_elem))
                        art_get_method_name_by_method_id *((void**)($method_array_fist_elem))
                        printf "\n"
                        set $method_array_fist_elem = (size_t)($method_array_fist_elem) + sizeof(void*)
                        set $idx = $idx + 1
                    end
                end
            end
            set $index = $index + 1
        end
        printf "\n"
    else
        printf "THIS CLASS HAVE NO iftable_\n"
    end
end

define class_print_vtable

    set $myclass = ('art::mirror::Class' *)$arg0
    printf "\nCLASS NAME:   "
    class_print_name_ $myclass

    set $vtable = ('art::mirror::PointerArray'*)($myclass->vtable_.reference_)

    if $vtable != 0
        set $method_array_len = $vtable->length_
        set $method_array_fist_elem = $vtable->first_element_
        printf "     first0: %p \n",$method_array_fist_elem

        if sizeof(void*) == 8
            set $method_array_fist_elem = (size_t)($method_array_fist_elem)+4
        end

        printf "     first1: %p \n",$method_array_fist_elem
        set $idx = (int) 0

        while $idx < $method_array_len
            printf "     ArtMethod[%02d][0x%010lx]: ",$idx,*((void**)($method_array_fist_elem))
            art_get_method_name_by_method_id *((void**)($method_array_fist_elem))
            printf "\n"
            set $method_array_fist_elem = (size_t)($method_array_fist_elem) + sizeof(void*)
            set $idx = $idx + 1
        end
        printf "\n"
    else
        set $is_primitive = (size_t)0
        set $is_interface = (size_t)0
        set $is_abstract = (size_t)0
        set $is_array_class = (size_t)0

        set $kPrimitiveTypeMask = (size_t)((1 << 16) - 1)
        if ($myclass->primitive_type_ & $kPrimitiveTypeMask) != 0
            set $is_primitive = (size_t)1
        end

        set $acc_flag = $myclass->access_flags_

        if ($acc_flag & 0x0400) != 0
            set $is_abstract = (size_t)1
        end

        if ($acc_flag & 0x0200) != 0
            set $is_interface = (size_t)1
        end

        if $myclass->component_type_.reference_ != 0
            set $is_array_class = (size_t)1
        end

        set $is_instantiable = (int)0

        if ($is_primitive + $is_interface + $is_abstract) == 0
            set $is_instantiable = (int)1
        else
            if ($is_abstract + $is_array_class) == 2
                set $is_instantiable = (int)1
            end
        end

        if $is_instantiable != 0

            set $embedded_vtable_len = *((uint32_t*)((size_t)$myclass + sizeof('art::mirror::Class')))

            printf "This Class have no vtable, print EmbeddedVtable[%d]:\n",$embedded_vtable_len

            set $imt_ptr_offset = (int)124
            if sizeof(void*) == 8
                set $imt_ptr_offset = (int)128
            end
            set $fist_method_addr = (size_t)$myclass + $imt_ptr_offset + sizeof(void*)

            p /x $fist_method_addr


            set $idx = (int) 0

            while $idx < $embedded_vtable_len
                printf "     ArtMethod[%02d][0x%010lx]: ",$idx,*((void**)($fist_method_addr))
                art_get_method_name_by_method_id *((void**)($fist_method_addr))
                printf "\n"
                set $fist_method_addr = (size_t)($fist_method_addr) + sizeof(void*)
                set $idx = $idx + 1
            end
            printf "\n"
        else
             printf "This class should not have Embedded Vtable.\n"
        end
    
    end

end

define class_print_methods_

    set $myclass = ('art::mirror::Class' *)$arg0
    printf "\nCLASS NAME:   "
    class_print_name_ $myclass

    set $length_prefixed_method_array = ('art::LengthPrefixedArray<art::ArtMethod>'*)($myclass->methods_)
    set $size = $length_prefixed_method_array->size_
# 8.0
#    set $first_method = (size_t)($length_prefixed_method_array->data) + 4

#7.0
    set $first_method = (size_t)($length_prefixed_method_array->data)

    set $art_method_size = (int)sizeof('art::ArtMethod')

    set $index = (int)0
    while $index < $size
        set $art_method = ('art::ArtMethod'*)($first_method)
        printf "     ArtMethod[%02d][0x%010lx]: ",$index,$first_method
        art_get_method_name_by_method_id $art_method
        printf "\n"
        set $first_method = $first_method + $art_method_size
        set $index = $index + 1
    end

    printf "\n"
end

define class_print_imt

    set $kSize = (int)43    
    set $myclass = ('art::mirror::Class' *)$arg0
    printf "\nCLASS NAME:   "
    class_print_name_ $myclass


    set $is_primitive = (size_t)0
    set $is_interface = (size_t)0
    set $is_abstract = (size_t)0
    set $is_array_class = (size_t)0

    set $kPrimitiveTypeMask = (size_t)((1 << 16) - 1)
    if ($myclass->primitive_type_ & $kPrimitiveTypeMask) != 0
        set $is_primitive = (size_t)1
    end

    set $acc_flag = $myclass->access_flags_

    if ($acc_flag & 0x0400) != 0
        set $is_abstract = (size_t)1
    end

    if ($acc_flag & 0x0200) != 0
        set $is_interface = (size_t)1
    end

    if $myclass->component_type_.reference_ != 0
        set $is_array_class = (size_t)1
    end

    set $is_instantiable = (int)0

    if ($is_primitive + $is_interface + $is_abstract) == 0
        set $is_instantiable = (int)1
    else
        if ($is_abstract + $is_array_class) == 2
            set $is_instantiable = (int)1
        end

    end

    if $is_instantiable != 0

        set $imt_ptr_offset = (int)124
        if sizeof(void*) == 8
            set $imt_ptr_offset = (int)128
        end

        set $first_method_addr = *(void**)((size_t)($arg0) + $imt_ptr_offset)

        p /x $first_method_addr

        if $first_method_addr != 0 

            set $index = (int)0
            while $index < $kSize

                set $art_method = ('art::ArtMethod'*)(*(void**)$first_method_addr)

                printf "     ArtMethod[%02d][0x%010lx]: ", $index,$art_method

                if $art_method->dex_method_index_ == 4294967295
                    printf " dex_method_idx[%p]", 4294967295
                    if $art_method == 'art::Runtime'::instance_->resolution_method_
                        printf ", resolution_method_"
                    end

                    if $art_method == 'art::Runtime'::instance_->imt_conflict_method_
                        printf ", imt_conflict_method_"
                    end

                    if $art_method == 'art::Runtime'::instance_->imt_unimplemented_method_
                        printf ", imt_unimplemented_method_"
                    end

                    if $art_method == 'art::Runtime'::instance_->callee_save_methods_[0]
                        printf ", callee_save_methods_[kSaveAllCalleeSaves]"
                    end

                    if $art_method == 'art::Runtime'::instance_->callee_save_methods_[1]
                        printf ", callee_save_methods_[kSaveRefsOnly]"
                    end

                    if $art_method == 'art::Runtime'::instance_->callee_save_methods_[2]
                        printf ", callee_save_methods_[kSaveRefsAndArgs]"
                    end

                    if $art_method == 'art::Runtime'::instance_->callee_save_methods_[3]
                        printf ", callee_save_methods_[kSaveEverything]"
                    end
                else
                    art_get_method_name_by_method_id $art_method
                end
                printf "\n"
                set $first_method_addr = $first_method_addr + sizeof(void*)
                set $index = $index + 1
            end
        else
            printf "this class have EMPTY IMT."
        end

    else
        printf "This class should not have IMT.\n"

    end

    printf "\n"
end




define art_get_java_stack_by_env
    set $thread = (('art::JNIEnvExt' *)$arg0)->self
    set $managed_stack = $thread->tlsPtr_.managed_stack->link_
    set $curfp = $thread->tlsPtr_.managed_stack.top_quick_frame_
    set $depth = 0

    art_get_java_stack
end


define art_get_java_stack_by_thread
    set $thread = ('art::Thread' *)$arg0
    set $managed_stack = $thread->tlsPtr_.managed_stack->link_
    set $curfp = $thread->tlsPtr_.managed_stack.top_quick_frame_
    set $depth = 0

    art_get_java_stack
end

define art_get_java_stack_at_crash64
    set $thread = ('art::Thread' *)$x18
    set $managed_stack = $thread->tlsPtr_.managed_stack->link_
    set $curfp = $sp
    set $depth = 0

    art_get_java_stack
end

define art_get_java_stack_at_crash32
    set $thread = ('art::Thread' *)$r9
    set $managed_stack = $thread->tlsPtr_.managed_stack->link_
    set $curfp = $sp
    set $depth = 0

    art_get_java_stack
end


define art_get_java_stack

   if *(void**)$curfp == 0
        set $curfp = $managed_stack->top_quick_frame_
        if $curfp == 0 
            printf "finished!!!\n"
            finish
        else
            printf "=== Next Managed Stack ===\n"
            set $managed_stack = $managed_stack->link_
        end
    end

    printf "Current FP\t %p\n", $curfp
    
    set  $artmethod = ('art::ArtMethod' *)(*((void** )$curfp))

    printf "Art Method\t %p\n", $artmethod

    if sizeof(size_t) == 8
        set $ptrsizedfields = ('art::ArtMethod::PtrSizedFields' *)(((size_t)&($artmethod->ptr_sized_fields_) + sizeof(size_t) - 1)/sizeof(size_t)*sizeof(size_t))
    else
        set $ptrsizedfields = $artmethod->ptr_sized_fields_
    end

    set $quickcode = (int*) ((size_t)$ptrsizedfields.entry_point_from_quick_compiled_code_ & 0xFFFFFFFFFFFFFFFE)

    printf "Quick Code\t %p\n", $quickcode

    set $framesize = *($quickcode - 4)

    printf "Frame Size\t 0x%x\n", $framesize

    set $returnpc = *(unsigned int **)((size_t)$curfp + (size_t)$framesize - sizeof(void*))
    printf "Return PC\t %p\n", $returnpc

  
    set $nextfp = (size_t)$curfp + (size_t)$framesize
    printf "Next FP\t\t %p\n", $nextfp

    printf "#%02d ", $depth

    art_get_method_name_by_method_id_address $curfp
    printf "\n"

    set $curfp = $nextfp
    set $depth = $depth +1

    art_get_java_stack
end

