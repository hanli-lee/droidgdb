define demo
  set $local_string = ('art::mirror::String' *) $arg0
  set $string_length  = (int) $local_string->count_

  set $declaringstr = (char*)($local_string->value_)

  set $logcal_index = (int) 0
  set $string_length = (int) 2*$string_length

  while $logcal_index < $string_length
    printf "%c", *($declaringstr + $logcal_index)
    set $logcal_index = $logcal_index + 2
  end

end

define ah_print_large_obj_space
    p 'art::Runtime'::instance_->heap_->large_object_space_
    set $cstr = 'art::Runtime'::instance_->heap_->large_object_space_->name_->__r_->__first_->__r->__words[2]
    set $str_size = 'art::Runtime'::instance_->heap_->large_object_space_->name_->__r_->__first_->__r->__words[1]
    printf "0x%x",(size_t)'art::Runtime'::instance_->heap_->large_object_space_->begin_
    printf " -- 0x%x  ",(size_t)'art::Runtime'::instance_->heap_->large_object_space_->end_
    art_print_cstring $cstr $str_size
    printf "\n"
end

define ah_print_continuous_space
    set $continuous_space = ('art::gc::space::ContinuousSpace'*)$arg0
    printf "0x%x",(size_t)$continuous_space->begin_
    printf " -- 0x%x -- ",(size_t)$continuous_space->end_
    printf "0x%x  ",(size_t)$continuous_space->limit_
    set $str_size = (int)0
    set $cstr = $continuous_space->name_->__r_->__first_->__r->__words[2]
    set $str_size = $continuous_space->name_->__r_->__first_->__r->__words[1]
    art_print_cstring $cstr $str_size
    printf "\n"
end
define ah_print_all_continuous_spaces
  set $space_begin = ('art::Runtime'::instance_->heap_->continuous_spaces_->__begin_)
  set $space_end = ('art::Runtime'::instance_->heap_->continuous_spaces_->__end_)
  set $main_space_backup = ('art::Runtime'::instance_->heap_->main_space_backup_.__ptr_.__first_)
  p /x $space_begin
  p /x $space_end
  if $main_space_backup != 0
      ah_print_continuous_space $main_space_backup
  end
  while $space_begin < $space_end
    set $addr = (size_t*)$space_begin
    ah_print_continuous_space *$addr
    set $space_begin = $space_begin + 1
  end

end

define ah_print_mark_bitmap
    p 'art::Runtime'::instance_->heap_->mark_bitmap_.__ptr_.__first_
end

define ah_print_live_bitmap
    p 'art::Runtime'::instance_->heap_->live_bitmap_.__ptr_.__first_
end

define ah_get_runtime_addr
  p 'art::Runtime'::instance_
end

define ah_print_runtime
  p *'art::Runtime'::instance_
end

define ah_get_heap_addr
  p 'art::Runtime'::instance_->heap_
end

define ah_print_heap
  p *'art::Runtime'::instance_->heap_
end

define ah_print_rosalloc_space
  p *'art::Runtime'::instance_->heap_->rosalloc_space_
end

define ah_print_rosalloc
  p *'art::Runtime'::instance_->heap_->rosalloc_space_->rosalloc_
end

define ah_print_run_by_addr
  set $addr = $arg0
  set $rosalloc = 'art::Runtime'::instance_->heap_->rosalloc_space_->rosalloc_
  if $rosalloc->base_ <= $addr && $rosalloc->base_ + $rosalloc->max_capacity_ >= $addr
    set $offset = (size_t)((size_t)$addr - (size_t)$rosalloc->base_)
    set $pm_index =  $offset / art::kPageSize
    set $page_map = $rosalloc->page_map_

        ##  // The types of page map entries.
        ##  enum PageMapKind {
        ##    kPageMapReleased = 0,     // Zero and released back to the OS.
        ##    kPageMapEmpty,            // Zero but probably dirty.
        ##    kPageMapRun,              // The beginning of a run.
        ##    kPageMapRunPart,          // The non-beginning part of a run.
        ##    kPageMapLargeObject,      // The beginning of a large object.
        ##    kPageMapLargeObjectPart,  // The non-beginning part of a large object.
        ##  };

    if *($page_map + $pm_index) == 2
      set $run = ('art::gc::allocator::RosAlloc::Run' *) ($rosalloc->base_ + $pm_index * art::kPageSize) 
      p *$run
      set $bracket_idx_ = $run->size_bracket_idx_
      set $free_bit_map_ = (uint32_t*)0
      if $run->is_thread_local_ == 1 
        set $free_bit_map_ = (uint32_t*)((uint8_t*)$run + 'art::gc::allocator::RosAlloc'::threadLocalFreeBitMapOffsets[$bracket_idx_])
      else
        set $free_bit_map_ = (uint32_t*)((uint8_t*)$run + 'art::gc::allocator::RosAlloc'::bulkFreeBitMapOffsets[$bracket_idx_])
      end

      set $header_size = 'art::gc::allocator::RosAlloc'::headerSizes[$bracket_idx_] 
      set $bracket_size = 'art::gc::allocator::RosAlloc'::bracketSizes[$bracket_idx_]
      set $slot_num = 'art::gc::allocator::RosAlloc'::numOfSlots[$bracket_idx_]
	  printf "bracket size=0x%x\n",$bracket_size
	  printf "slot size=%d\n",($slot_num+1)
	  printf "\nalloc bitmap:\n"
      set $i = 0
      while $i < ($slot_num + 31)/32
	      x /wx $run->alloc_bit_map_ + $i
		  set $i = $i + 1
	  end

	  printf "\nfree bitmap:\n"
      set $i = 0
      while $i < ($slot_num + 31)/32
	      x /wx $free_bit_map_ + $i
		  set $i = $i + 1
	  end
	  printf "\n"

      printf "run start: 0x%08x, end: 0x%08x\n\n", (size_t)$run, ((size_t)$run + $header_size + $bracket_size * ($slot_num + 1))

      set $i = (int)0

      set $addr_off = (int)((size_t)$addr - (size_t)$run - (size_t)$header_size)
    
      if $addr_off < (int)0
        set $start = (int)0
      else
        set $start = (int)($addr_off/$bracket_size) - 5
      end

      if $start >= $i
        set $i = $start
      end

      while $i < $start+10
        if $i >= $slot_num+1
            break
        end
        set $slot_addr = (size_t)$run + $header_size + $bracket_size * $i

        if $slot_addr <= $addr && $slot_addr + $bracket_size > $addr
            printf "**********************************************\n" 
        end

        set $alloc_bitmap = $run->alloc_bit_map_[$i/32]
        set $free_bitmap = $free_bit_map_[$i/32]

        set $j = (int)0
        set $len = $bracket_size/16
        while $j < $len
          set $address = $slot_addr+16*$j
          printf "%p:    0x%08x    0x%08x    0x%08x    0x%08x    ", $address, *($address), *($address+4), *($address+8), *($address+12)
          if $j == 0
		    printf "slot = %03d, state = ", (int)$i
            if ($alloc_bitmap >> ($i % 32)) & 0x1 == 0x1
                if ($free_bitmap >> ($i % 32)) & 0x1 == 0x1
                  printf "MERGE"
                else
                  printf "ALLOC"
                end
            else
              printf "FREE"
            end
          end
          if $len >= 1 && $j <= $len - 1
            printf "\n"
          end
          set $j = $j + 1
        end 

        if $slot_addr <= $addr && $slot_addr + $bracket_size > $addr
            printf "**********************************************\n"
        end

        if $len > 1
            printf "\n"
        end

        set $i = $i + 1
      end
    else
        printf "%s is not rosalloc space type=%d!\n", $addr,*($page_map + $pm_index)
    end
  end
end

