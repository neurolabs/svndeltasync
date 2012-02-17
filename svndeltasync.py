#!/usr/bin/env python
# coding: utf-8

from lxml import etree
from lxml import objectify
import getopt
import sys
import os
import subprocess
import shutil

#class Chdir:         
#    def __init__( self, newPath ):
#        try:
#           self.savedPath = os.getcwd()
#           os.chdir(newPath)
#        except:
#           print("Error: source directory does not exist
#           sys.exit(3)
#
#    def __del__( self ):
#        os.chdir( self.savedPath )

def usage():
    print '''Usage: svndelta.py source-dir destination-dir
Parameters:
    -s, --source-dir The source directory to sync the svn in
    -d, --dest-dir   The directory to sync to
'''

def main(argv):
    # args
    try:                                
        opts, args = getopt.getopt(argv, "")
    except getopt.GetoptError:           
        usage()                          
        sys.exit(1)
    try:
        if len(args) != 2:
            print("Error: wrong number of parameters.")
            usage()
            sys.exit(1)
        source = args[0] 
        destination = args[1]

        if (not os.path.isdir(destination)):
            raise Exception("Error, destination is not a directory " + destination)

        chdir(source)

        checkForSvnRepo()

        preRevision = getCurrentRevision()


        syncSvn()

        postRevision = getCurrentRevision()

        if preRevision < postRevision:

            print "handling update from revision {0} to {1}".format(preRevision, postRevision)
            changedfiles = getFilesChanged(preRevision, postRevision)
            deletedfiles = getFilesDeleted(preRevision, postRevision)

            for file in changedfiles:
                copyFile(file, source, destination)

            for file in deletedFiles:
                deleteFile(file, destination)

        else:
            print "No Changes, not syncing"
    except Exception as ex:
        print("Error: " + str(ex))
        if (preRevision != None):
            print("Rolling back working copy to revision " + preRevision)
            syncSvn(preRevision)
        sys.exit(1)

def getFilesChanged(fro, to):
    return getFilesOfActions([ "M", "A", "R" ], fro, to)

def getFilesDeleted(fro, to):
    return getFilesOfActions([ "D" ], fro, to)

def getFilesOfActions(actions, fro, to):
    changelog = execute(["svn", "log", "-r", str(int(fro)+1)+":"+str(to), "-v", "--xml"])[0]
    files = []

    root = objectify.fromstring(changelog);

    for path in root.xpath('/log/logentry/paths/path'):
        action = path.get("action")
        if (action in actions):
            file = path.__str__()
            files.append(file)
            if (action == "M"):
                print("file changed: " + file)

    # deduplication
    return list(set(files))

def copyFile(file, sourceDir, targetDir):
    # subversion also shows directory creates, we can ignore those
    if (os.path.isfile(sourceDir + file)):
        relativePath = os.path.dirname(file)
        targetPath = targetDir + relativePath
        if (not os.path.isdir(targetPath)):
            os.makedirs(targetPath)
        sourceFile = sourceDir + file
        destFile = targetDir + file
        
        print "Copying " + sourceFile + " to " + destFile 
        shutil.copyfile(sourceFile, destFile)

def deleteFile(file, destDir):
    path = destDir + file
    if (os.path.exists(path):
        if (os.path.isdir(path)):
            os.rmdir(path)
        else:
            os.delete(path)

def chdir(path):
    if os.path.isdir(path) == True:
        os.chdir(path)
    else:
        raise Exception("Error, path is not a directory: " + path)

def checkForSvnRepo():
    execute(["svn", "info"])

def getCurrentRevision():
    return execute(["svnversion"])[0].strip()

def syncSvn(rev=None):
    command = ["svn", "up"]
    if (rev != None):
        command.append("-r")
        command.append(rev)
    execute(command)
    
def execute(cmdList):
    try:
        process = subprocess.Popen(cmdList, stdout=subprocess.PIPE)
        return process.communicate()
    except:
       raise Exception("Error, call failed: " + str(cmdList))

if __name__ == "__main__":
    main(sys.argv[1:])
