import sublime
import sublime_plugin
import os
import shutil
import threading

ossettings = sublime.load_settings('os_specific_user_files.sublime-settings')
osplatform = sublime.platform()
user = os.path.join(sublime.packages_path(), 'User')
ospath = os.path.join(user, 'OsSpecificUserFiles', osplatform)
running_thread = False


def os_specific_alert():
    sublime.error_message('OS Specific User Files encountered one or more errors.\nPlease see the console for more info.')


def run_copy_thread(force=False):
    if not running_thread:
        t = CopyOsUserFiles(ossettings.get(osplatform, {}), force)
        t.start()


def run_backup_thread(force=False):
    if not running_thread:
        t = BackupOsUserFiles(ossettings.get(osplatform, {}), force)
        t.start()


def copy_file(src, dest):
    status = False
    try:
        shutil.copyfile(src, dest)
        print "OS Specific User Files: SUCCESS - Copied to User: %s" % src
    except:
        print "OS Specific User Files: ERROR - Could not copy file: %d" % src
        status = True
    return status


def copy_directory(src, dest):
    status = False
    try:
        if os.path.exists(dest):
            print "OS Specific User Files: REMOVING - Directory already exists: %s" % dest
            shutil.rmtree(dest)
    except:
        print "OS Specific User Files: ERROR - Could not remove: %s" % dest
        status = True
        return status

    try:
        shutil.copytree(src, dest)
        print "OS Specific User Files: SUCCESS - Copied to User: %s" % src
    except:
        print "OS Specific User Files: ERROR - Could not copy directory: %d" % src
        status = True
    return status


def move_files(src, dest):
    status = False
    if os.path.exists(dest):
        if os.path.isdir(dest):
            try:
                if os.path.exists(dest):
                    print "OS Specific User Files: REMOVING - Directory already exists: %s" % dest
                    shutil.rmtree(dest)
            except:
                print "OS Specific User Files: ERROR - Could not remove: %s" % dest
                status = True
                return status
        else:
            try:
                print "OS Specific User Files: REMOVING - File already exists: %s" % dest
                os.remove(dest)
            except:
                print "OS Specific User Files: ERROR - Could not remove: %s" % dest
                status = True
                return status
    try:
        shutil.move(src, dest)
    except:
        print "OS Specific User Files: ERROR - Could not move %s" % src
        status = True
    return status


class OsUserFiles(threading.Thread):
    def __init__(self, file_list, force=False):
        self.force = force
        self.file_list = file_list
        threading.Thread.__init__(self)

    def run(self):
        global running_thread
        running_thread = True
        self.copy_all()
        running_thread = False


class BackupOsUserFiles(OsUserFiles):
    def __init__(self, file_list, force=False):
        OsUserFiles.__init__(self, file_list, force)

    def copy_all(self):
        errors = False
        # Copy single files
        for item in self.file_list['files']:
            key = os.path.normpath(item)
            value = os.path.normpath(self.file_list['files'][item])
            dest = os.path.join(ospath, key)
            src = os.path.join(user, value)

            if os.path.exists(src):
                errors |= copy_file(src, dest)

        # Copy directories
        for item in self.file_list['directories']:
            key = os.path.normpath(item)
            value = os.path.normpath(self.file_list['directories'][item])
            dest = os.path.join(ospath, key)
            src = os.path.join(user, value)

            if os.path.exists(src):
                errors |= copy_directory(src, dest)

        # Rename files
        for item in self.file_list['rename']:
            key = os.path.normpath(item)
            value = os.path.normpath(self.file_list['rename'][item])
            dest = os.path.join(ospath, key)
            src = os.path.join(ospath, value)

            if os.path.exists(src):
                errors |= move_files(src, dest)

        if errors:
            os_specific_alert()


class CopyOsUserFiles(OsUserFiles):
    def __init__(self, file_list, force=False):
        OsUserFiles.__init__(self, file_list, force)

    def copy_all(self):
        errors = False
        # Copy single files
        for item in self.file_list['files']:
            key = os.path.normpath(item)
            value = os.path.normpath(self.file_list['files'][item])
            src = os.path.join(ospath, key)
            dest_dir = os.path.join(user, os.path.dirname(value))
            dest = os.path.join(user, value)

            if (not os.path.exists(dest) or self.force) and os.path.exists(src) and os.path.exists(dest_dir):
                errors |= copy_file(src, dest)

        # Copy directories
        for item in self.file_list['directories']:
            key = os.path.normpath(item)
            value = os.path.normpath(self.file_list['directories'][item])
            src = os.path.join(ospath, key)
            dest_dir = os.path.join(user, os.path.dirname(value))
            dest = os.path.join(user, value)

            if (not os.path.exists(dest) or self.force) and os.path.exists(src) and os.path.exists(dest_dir):
                errors |= copy_directory(src, dest)

        # Rename files
        for item in self.file_list['rename']:
            key = os.path.normpath(item)
            value = os.path.normpath(self.file_list['rename'][item])
            src = os.path.join(user, key)
            dest = os.path.join(user, value)

            if (not os.path.exists(dest) or self.force) and os.path.exists(src):
                errors |= move_files(src, dest)

        if errors:
            os_specific_alert()


class BackupOsUserFilesCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        print "OS Specific User Files: Backing up User to OsSpecificUserFiles..."
        run_backup_thread(force=True)


class CopyOsUserFilesCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        print "OS Specific User Files: Copying files to User..."
        run_copy_thread(force=True)


print "OS Specific User Files: Checking for files that have never been copied over..."
run_copy_thread(force=False)
