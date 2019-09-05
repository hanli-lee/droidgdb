#!/bin/bash

#source_dir="/home/mi/source/7.0/aqua-n-dev/"
#source_dir="/home/mi/disk2/9.0/D5X2/"
source_dir="/home/mi/disk2/8.0/sagit-o-dev/"
#source_dir="/home/mi/disk2/6.0/v7-m-cancro-dev/"

gdb=$source_dir"prebuilts/gdb/linux-x86/bin/gdb"
gdbserver_path=$source_dir"prebuilts/misc/android-arm/gdbserver/gdbserver"
gdbserver64_path=$source_dir"prebuilts/misc/android-arm64/gdbserver64/gdbserver64"
gdbserver="/data/local/tmp/gdbserver"
gdbserver64="/data/local/tmp/gdbserver64"


SOURCE="${BASH_SOURCE[0]}"
    while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
        DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
        SOURCE="$(readlink "$SOURCE")"
        [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
    done
CURRENT_DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"


SCRIPT_FILE=$CURRENT_DIR"/gdb-script/init.gdb"
SCRIPT_FILE0=$CURRENT_DIR"/gdb-script/art.gdb"
SCRIPT_FILE1=$CURRENT_DIR"/gdb-script/art_heap.gdb"
SHADOW_FILE=$CURRENT_DIR"/shadow/gdb_driver.py"

echo $CURRENT_DIR

function usage() {

    echo "-------------------------------"
    echo "   Usage:"
    echo "       1.driod [core/core64] [symbol-dir] [core-file] [file]"
    echo "               *symbol-dir, like       : ~/out/target/product/xxx/symbols/"
    echo "               *core-file, like        : ~/LOG/core-HeapTaskDaemon-2806"
    echo "               *file, this arg is neccessary while debug a native process, like : dex2oat"
    echo -e ""
    echo "       2.droid [attach] [symbol-dir] [pid/processName]"
    echo "               $ droid attach ~/out/target/product/xxx/symbols/ zygote64"
    echo "               both JAVA & NATIVE process supported now."
    echo -e ""
    echo "       3.droid [debug] [arm/arm64] [executable]"
    echo "               $ droid debug arm64 hello"
    echo "               not supported now."
    echo -e ""
    echo "       4.droid h"
    echo "               print droid cmd history"
    echo -e ""
    exit

}

if [ $# -lt 1 ]; then
usage
fi

function get_history_file() {
    script_file=`dirname $0`"/droid"
    real_file=""
    while [ 1 ]
    do
        real_file=`ls -ld $script_file | awk '{print $NF}'`
        if [ "$real_file" = "$script_file" ]; then
            break
        fi
        script_file=$real_file
    done
    history_file=${real_file%/*}"/.droid_history.txt"
    echo "$history_file"
}

history_file=`get_history_file`

function droid_core() {

    symdir=$1
    coredump=$2
    inst_set=$3
    debug_bin=$4
    cmd_arg4=""
    cur_dir=`pwd`

    if [[ ${symdir:0:6} != "/home/" ]]; then
        if [[ $symdir != *$cur_dir* ]]; then
            symdir=$cur_dir"/"$symdir
        fi
#if [[ $coredump != *$cur_dir* ]]; then
        if [[ $coredump != */home/* ]]; then
            coredump=$cur_dir"/"$coredump
        fi
    fi

    symdir=${symdir//\/.\//\/}
    symdir=${symdir//\/\//\/}
    coredump=${coredump//\/.\//\/}
    coredump=${coredump//\/\//\/}

    bin_path=$symdir"/system/bin/"

    if [ "$debug_bin" = "java32" ]; then
        bin=$bin_path"app_process32"
    elif [ "$debug_bin" = "java64" ]; then
        bin=$bin_path"app_process64"
    else
        bin=$bin_path"$debug_bin"
        cmd_arg4=" "$debug_bin
    fi

    if [ "core64" = "$inst_set" ]; then
        solib_path=$symdir"/system/lib64/"
    elif [ "core" = "$inst_set" ]; then
        solib_path=$symdir"/system/lib/"
    fi

    bin=${bin//\/.\//\/}
    bin=${bin//\/\//\/}
    solib_path=${solib_path//\/.\//\/}
    solib_path=${solib_path//\/\//\/}
    bin_path=${bin_path//\/.\//\/}
    bin_path=${bin_path//\/\//\/}

    echo $bin
    echo $solib_path
    echo $bin_path
    echo $coredump

    if [ ! -f "$bin" ]; then
        echo "exec file: "$bin" do not exist"
        return
    fi
    if [ ! -f "$coredump" ]; then
        echo "coredump: "$coredump" do not exist"
        return
    fi
    if [ ! -d "$solib_path" ]; then
        echo "solib path: "$solib_path" do not exist"
        return
    fi
    if [ ! -d "$bin_path" ]; then
        echo "bin path: "$bin_path" do not exist"
        return
    fi

    if [ ! -f "$history_file" ]; then
        touch "$history_file"
    fi

    history_cmd="droid "$inst_set" "$symdir" "$coredump$cmd_arg4
    write_history="yes"

    while read line
    do
        if [ "$line" = "$history_cmd" ]; then
            write_history="no"
            break
        fi
    done < $history_file

    if [ "$write_history" = "yes" ]; then
        echo -e "$history_cmd" >> $history_file
    fi


    $gdb --ex="file $bin" --ex="set solib-search-path $solib_path:$bin_path" --ex="set solib-absolute-prefix $solib_path:$bin_path" --ex="dir $source_dir" --ex="core-file $coredump" --ex="bt" --ex="set print pretty on" --ex="source $SHADOW_FILE" --ex="source $SCRIPT_FILE" --ex="source $SCRIPT_FILE0" --ex="source $SCRIPT_FILE1"
}

function get_proc_pid() {

    process=$1

    pid=`adb shell ps  | grep "$process"|grep -v "$0"|grep -v "grep"| awk '{print $2}'`
    echo $pid
}

function get_proc_ppid() {

    process=$1

    case "$process" in
        [1-9][0-9]*)  # 1. grep by pid
            ppid=`adb shell ps  | grep "$process"|grep -v "$0"|grep -v "grep"| awk '{FS=" "}{if ($2=='$process') print $3}'`
        ;;
        *)  # 2. grep by process name
            ppid=`adb shell ps  | grep "$process"|grep -v "$0"|grep -v "grep"| awk '{print $3}'`
        ;;
    esac
    echo $ppid
}

function get_proc_name() {

    process=$1
    case "$process" in
        [1-9][0-9]*)  # 1. grep by pid
            proc_name=`adb shell ps  | grep "$process"|grep -v "$0"|grep -v "grep"| awk '{FS=" "}{if ($2=='$process') print $9}'`
        ;;
        *)  # 2. grep by process name
            proc_name=`adb shell ps  | grep "$process"|grep -v "$0"|grep -v "grep"| awk '{print $9}'`
        ;;
    esac
    echo $proc_name
}

function droid_attach() {

    root=`adb root`
    if [[ $? == 0 ]]; then
        if [[ $root =~ "adbd cannot run as root" ]]; then
            echo -e "\n\n---ONLY ROOT COULD ATTACH PROCESS---\n\n"
            exit
        else
            echo -e ""
        fi
    else
        echo -e "\n\n---NO DEVICES/EMULATORS FOUND---\n\n"
        exit
    fi

    adb shell setenforce 0
    a=`adb push $gdbserver_path $gdbserver`
    a=`adb push $gdbserver64_path $gdbserver64`

    symdir=$1
    pid=$2

    process="zygote"
    zygote_pids=`get_proc_pid $process`
    for single in $zygote_pids
        do
            env_path="/proc/"$single"/environ"
            env=`adb shell cat $env_path`
            if [[ $env =~ "ANDROID_SOCKET_zygote=" ]]; then
                zygote64_pid=$single
            elif [[ $env =~ "ANDROID_SOCKET_zygote_secondary=" ]]; then
                zygote32_pid=$single
            else
                fake_zygote=$single
            fi
        done
    echo -e "zygote32: "$zygote32_pid", zygote64: "$zygote64_pid

    case "$pid" in
        [1-9][0-9]*)
            ppid=`get_proc_ppid $pid`
            proc_name=`get_proc_name $pid`
            if [ "$proc_name" = "" ]; then
                echo -e "ERROE, invalid pid : "$pid", did not found."
                return
            fi
#            echo -e "proc name: "$proc_name"\npid: "$pid"\nppid: "$ppid
        ;;
        *)
            input_proc_name=$pid
            if [ "$input_proc_name" = "" ]; then
                echo -e "ERROR, you'd better input a unique pid or process name\n"
                return
            elif [ "$input_proc_name" = "zygote" ]; then
                pid=$zygote32_pid
                ppid=1
                proc_name=$input_proc_name
            elif [ "$input_proc_name" = "zygote64" ]; then
                pid=$zygote64_pid
                ppid=1
                proc_name=$input_proc_name
            else
                pid=`get_proc_pid $input_proc_name`
                declare -i count
                count=0
                for single in $pid
                    do
                        count=$count+1
                    done
                if [ $count -ne 1 ]; then
                    echo -e "ERROR, there are ["$count"] process match: "$input_proc_name": "$pid
                    echo -e "ERROR, you'd better input a unique pid or process name\n"
                    return
                fi
                ppid=`get_proc_ppid $input_proc_name`
                proc_name=`get_proc_name $input_proc_name`
            fi
        ;;
    esac

    echo -e "proc:       "$proc_name" , pid("$pid"), ppid("$ppid")\n"

    bin_path=$symdir"/system/bin/"
#    if (pid not in zygote, ppid not in zygote) native proc
    if [[ "$pid" != "$zygote32_pid"
          && "$pid" != "$zygote64_pid"
          && "$ppid" != "$zygote32_pid"
          && "$ppid" != "$zygote64_pid" ]]; then

          bin=$symdir$proc_name
          bin_path=${bin%/*}"/"

          is_64bit_bin=`file $bin | grep "64-bit"`
          if [ "$is_64bit_bin" = "" ]; then
              echo "INST SET:   32-bit"
              gdbserver=$gdbserver
              solib_path=$symdir"/system/lib/"
          else
              echo "INST SET:   64-bit"
              gdbserver=$gdbserver64
              solib_path=$symdir"/system/lib64/"
          fi

#aqua:/ # od -A x -N 6 -t x /system/bin/rild
#000000    464c457f    [00000102]
#aqua:/ # od -A x -N 6 -t x /system/bin/dex2oat
#000000    464c457f    [00000101]

    else
        solib_path=$symdir"/system/lib/"
        bin=$bin_path"app_process32"

        if [[ "$ppid" = "$zygote64_pid" || "$pid" = "$zygote64_pid" ]]; then
            gdbserver=$gdbserver64
            bin=$bin_path"app_process64"
            solib_path=$symdir"/system/lib64/"
        fi
    fi

    echo -e "gdbserver:  "$gdbserver"\nbin:        "$bin"\nbin_path:   "$bin_path"\nsolib:      "$solib_path"\n\n"

    sleep 1
    adb shell $gdbserver :1234 --attach $pid &
    adb forward tcp:1234 tcp:1234
    sleep 1
    echo -e "\n\n\n"
    $gdb --ex="file $bin" --ex="set solib-search-path $solib_path:$bin_path" --ex="set solib-absolute-prefix $solib_path:$bin_path" --ex="target remote localhost:1234" --ex="dir $source_dir" --ex="bt" --ex="set print pretty on" --ex="source $SCRIPT_FILE" --ex="source $SHADOW_FILE"  --ex="source $SCRIPT_FILE0" --ex="source $SCRIPT_FILE1"

}

function droid_debug() {

    root=`adb root`
    if [[ $? == 0 ]]; then
        if [[ $root =~ "adbd cannot run as root" ]]; then
            echo -e "\n\n---ONLY ROOT COULD DEBUG PROCESS---\n\n"
            exit
        else
            echo -e "\n\n"
        fi
    else
        echo -e "\n\n---NO DEVICES/EMULATORS FOUND---\n\n"
        exit
    fi

    adb shell setenforce 0
    a=`adb push $gdbserver_path $gdbserver`
    a=`adb push $gdbserver64_path $gdbserver64`

    symdir=$source_dir"out/target/product/aqua/symbols/"
    bin_path=$symdir"system/bin/"

    inst_set=$1
    bin=$bin_path$2

    if [ "arm64" = "$inst_set" ]; then
        solib_path=$symdir"/system/lib64/"
        gdbserver=$gdbserver64
    elif [ "arm" = "$inst_set" ]; then
        solib_path=$symdir"/system/lib/"
    fi

    echo -e "bin:        "$bin"\nsolib:      "$solib_path"\ngdbserver:  "$gdbserver"\n\n"

    sleep 1
echo $3
    adb shell $gdbserver :1234 $2 &
    adb forward tcp:1234 tcp:1234

    $gdb --ex="file $bin" --ex="set solib-search-path $solib_path:$bin_path" --ex="set solib-absolute-prefix $solib_path:$bin_path" --ex="target remote localhost:1234" --ex="dir $source_dir" --ex="bt" --ex="set print pretty on" --ex="source $SCRIPT_FILE" --ex="source $SHADOW_FILE"  --ex="source $SCRIPT_FILE0" --ex="source $SCRIPT_FILE1"

}

cmd=$1
case "$cmd" in
    "core")
        symdir=$2
        core_file=$3
        if [ $# -lt 4 ]; then
            debug_bin="java32"
        else
            debug_bin=$4
        fi
        droid_core $symdir $core_file core $debug_bin
        ;;
    "core64")
        symdir=$2
        core_file=$3
        if [ $# -lt 4 ]; then
            debug_bin="java64"
        else
            debug_bin=$4
        fi
        droid_core $symdir $core_file core64 $debug_bin
        ;;
    "attach")
        symdir=$2
        proc=$3
        bin=$4
        droid_attach $symdir $proc $bin
        ;;
    "debug")
        inst_set=$2
        bin=$3
        arg=$4
        droid_debug $inst_set $bin $arg
        ;;
    "-h")
        usage
        ;;
    "h")
        echo -e "cmd history: "
        declare -i count
        count=1
        if [ -f "$history_file" ]; then
            while read line
            do
                echo -e $count".\n"$line"\n"
                count=$count+1
            done < $history_file
        else
            echo "There is no history yet."
        fi
        ;;
    *)
        echo "unrecognized cmd: "$cmd
        usage
    ;;
esac

#  (anonymous namespace)::ForkAndSpecializeCommon
#  android::com_android_internal_os_Zygote_nativeForkAndSpecialize
#  Am.java: am set-debug-app -w --persistent processName (App process blocked at BindApplication)
#  ddms: $  jdb -attach localhost:8700
