# gdbserver-attach
a convenient script for gdbserver --attach and gdb core-file  debug.

# Usage:
       1.driod [core/core64] [symbol-dir] [core-file] [file]
               *symbol-dir, like       : ~/out/target/product/xxx/symbols/
               *core-file, like        : ~/LOG/core-HeapTaskDaemon-2806"
               *file, this arg is neccessary while debug a native process, like : dex2oat

       2.droid [attach] [symbol-dir] [pid/processName]
               $ droid attach ~/out/target/product/xxx/symbols/ zygote64
               both JAVA & NATIVE process supported now.

       3.droid [debug] [arm/arm64] [executable]
               $ droid debug arm64 hello
               not supported now.

       4.droid h
               print droid cmd history
