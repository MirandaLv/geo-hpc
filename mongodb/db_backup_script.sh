#!/bin/sh

# this script should be placed in:
#   /opt/aiddata/db_backup_script.sh
#
# with a crontab set:
#   1 1 * * * bash /opt/aiddata/db_backup_script.sh BRANCH
# where BRANCH is either "master" or "develop"
#
# requires ssh key be setup on server for aiddatageo

branch=$1

if [[ $branch == "" ]]; then
    exit 1
fi

timestamp=`date +%Y%m%d_%H%M%S`

backup_dir=/sciclone/aiddata10/REU/backups/mongodb_backups

# compresses individual items then archives
# example mongorestore:
#   mongorestore --gzip --archive=backup.archive
# for details see:
#   https://www.mongodb.com/blog/post/archiving-and-compression-in-mongodb-tools

mongodump --gzip --archive | ssh aiddatageo@vortex.sciclone.wm.edu "cat - > $backup_dir/$branch/$timestamp.archive"

