#!/bin/sh
#
# maildrop:  Start script to run the maildrop python process
#
# chkconfig: 345 97 03
# description:  This is a daemon which handles the task of emailing \
#               periodically the email left by a Zope server
#
# processname: maildrop
#
# Where is your Zope instance?
ZOPE_HOME="/usr/local/finsiel/Zope-2.7.6-final"

# Set the maildrop main directory
reldir=`dirname $0`

MAILDROP_HOME="$ZOPE_HOME/Products/SEMIDE/Tools/mdh"

# What SMTP server will maildrop use?
MAILDROP_SMTP="localhost"

# How long to wait between spool checkups?
MAILDROP_POLLING_INTERVAL=60

# Where is the python executable?
PYTHON_EXE="/usr/local/finsiel/bin/python2.3"
#PYTHON_EXE="$ZOPE_HOME/bin/python"

export MAILDROP_HOME ZOPE_HOME MAILDROP_SMTP MAILDROP_POLLING_INTERVAL
export PYTHON_EXE
RETVAL=0

start() {
# NOTE:
#
# If you add the "-d" flag to :the flags used to invoke the 
# maildrop.py script then all log output will be written to 
# the terminal along with the log file.

    exec $PYTHON_EXE $MAILDROP_HOME/maildrop.py \
         -h $ZOPE_HOME \
         -s $MAILDROP_SMTP \
         -i $MAILDROP_POLLING_INTERVAL #-d
}

stop() {
    # Where is the pid file?
    MAILDROP_PID=$ZOPE_HOME/var/maildrop/var/maildrop.pid

    # Extract the PIDs
    MAILDROP_PIDS=`cat $MAILDROP_PID`

    # Remove the pid file
    rm -f $MAILDROP_PID

    # Kill the process
    kill $MAILDROP_PIDS
}
# See how we were called.
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    status)
        status maildrop
        RETVAL=$?
        ;;
    restart)
        stop
        start
        ;;
    *)
        echo $"Usage: $0 {start|stop|status|restart}"
        ;;
esac
exit $RETVAL

